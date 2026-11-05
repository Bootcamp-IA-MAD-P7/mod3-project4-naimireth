"""Orquestacion del procesamiento de videos y consultas de resultados."""

import logging
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, sessionmaker

from app.database.models import Analysis, BrandResult, Detection, utcnow
from app.schemas.analysis import (
    AnalysisDetail,
    AnalysisProgress,
    AnalysisStatus,
    AnalysisSummary,
    DashboardBrandSummary,
    DashboardStats,
    PreviewFrame,
    PreviewResult,
)
from app.services.detector import BrandDetector
from app.services.metrics import compute_brand_metrics
from app.services.preview import PreviewWriter
from app.services.video_processor import VideoMetadata, iter_sampled_frames

logger = logging.getLogger(__name__)


class AnalysisNotFoundError(Exception):
    pass


class AnalysisService:
    def __init__(
        self,
        session_factory: sessionmaker,
        executor: ThreadPoolExecutor,
        detector_provider: Callable[[], BrandDetector | None],
        preview_dir: Path | None = None,
        preview_enabled: bool = True,
        preview_max_frames: int = 240,
        preview_slow_motion_fps: float = 1.0,
    ) -> None:
        self._session_factory = session_factory
        self._executor = executor
        self._detector_provider = detector_provider
        self._preview_dir = preview_dir
        self._preview_enabled = preview_enabled
        self._preview_max_frames = preview_max_frames
        self._preview_slow_motion_fps = preview_slow_motion_fps

    def create_analysis(
        self,
        video_name: str,
        source_reference: str,
        metadata: VideoMetadata,
    ) -> int:
        with self._session_factory() as session:
            analysis = Analysis(
                video_name=video_name,
                source_type="upload",
                source_reference=source_reference,
                status=AnalysisStatus.QUEUED.value,
                duration_seconds=metadata.duration_seconds or None,
                fps=metadata.fps,
                total_frames=metadata.total_frames or None,
                sampling_stride=metadata.sampling_stride,
                effective_fps=metadata.effective_fps,
                width=metadata.width or None,
                height=metadata.height or None,
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis.id

    def submit(self, analysis_id: int, file_path: Path, metadata: VideoMetadata) -> None:
        self._executor.submit(self._run, analysis_id, file_path, metadata)

    def _run(self, analysis_id: int, file_path: Path, metadata: VideoMetadata) -> None:
        try:
            self._process(analysis_id, file_path, metadata)
        except Exception as exc:
            logger.exception("Falló el análisis %s", analysis_id)
            self._clear_preview(analysis_id)
            self._mark_failed(analysis_id, exc)
        finally:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("No se pudo eliminar el archivo temporal %s", file_path)

    def _process(self, analysis_id: int, file_path: Path, metadata: VideoMetadata) -> None:
        detector = self._detector_provider()
        if detector is None:
            raise RuntimeError("El modelo YOLO no está cargado")

        brand_names = detector.class_names
        detected_frames: dict[str, int] = {}
        box_counts: dict[str, int] = {}
        total_raw_detections = 0
        pending_detections: list[Detection] = []
        last_source_index = 0
        last_commit = time.monotonic()
        preview_writer = (
            PreviewWriter(
                root=self._preview_dir,
                analysis_id=analysis_id,
                max_frames=self._preview_max_frames,
            )
            if self._preview_dir is not None
            and self._preview_enabled
            and self._preview_max_frames > 0
            else None
        )
        if preview_writer is not None:
            preview_writer.cleanup()

        with self._session_factory() as session:
            analysis = session.get(Analysis, analysis_id)
            if analysis is None:
                return

            analysis.status = AnalysisStatus.PROCESSING.value
            analysis.started_at = utcnow()
            analysis.progress = 0.0
            analysis.error_message = None
            session.commit()

            for sample_number, (frame_index, frame) in enumerate(
                iter_sampled_frames(file_path, metadata.sampling_stride), start=1
            ):
                last_source_index = frame_index
                frame_detections: dict[str, list[float]] = {}
                detected_boxes = detector.detect(frame)

                for detected_box in detected_boxes:
                    total_raw_detections += 1
                    current = frame_detections.get(detected_box.brand_name)
                    if current is None:
                        frame_detections[detected_box.brand_name] = [1.0, detected_box.confidence]
                    else:
                        current[0] += 1
                        current[1] = max(current[1], detected_box.confidence)

                if preview_writer is not None and detected_boxes:
                    try:
                        preview_writer.write(frame, detected_boxes, frame_index)
                    except Exception:
                        logger.warning(
                            "No se pudo guardar la vista previa del análisis %s",
                            analysis_id,
                            exc_info=True,
                        )
                        preview_writer = None

                timestamp_seconds = frame_index / metadata.fps
                for brand_name, (boxes, confidence) in frame_detections.items():
                    detected_frames[brand_name] = detected_frames.get(brand_name, 0) + 1
                    box_counts[brand_name] = box_counts.get(brand_name, 0) + int(boxes)
                    pending_detections.append(
                        Detection(
                            analysis_id=analysis_id,
                            brand_name=brand_name,
                            frame_index=frame_index,
                            timestamp_seconds=round(timestamp_seconds, 3),
                            confidence=round(float(confidence), 4),
                            box_count=int(boxes),
                        )
                    )

                now = time.monotonic()
                if sample_number % 10 == 0 or (now - last_commit) >= 1.5:
                    session.add_all(pending_detections)
                    pending_detections.clear()
                    analysis.processed_frames = frame_index + 1
                    analysis.progress = self._progress(frame_index + 1, metadata)
                    session.commit()
                    last_commit = now

            if pending_detections:
                session.add_all(pending_detections)

            total_source_frames = metadata.total_frames or (last_source_index + 1)
            duration_seconds = metadata.duration_seconds
            if duration_seconds <= 0 and metadata.fps > 0:
                duration_seconds = total_source_frames / metadata.fps

            metrics = compute_brand_metrics(
                detected_frames=detected_frames,
                box_counts=box_counts,
                duration_seconds=duration_seconds,
                effective_fps=metadata.effective_fps,
                brand_names=brand_names,
            )

            for metric in metrics:
                session.add(
                    BrandResult(
                        analysis_id=analysis_id,
                        brand_name=metric.brand_name,
                        frames_detected=metric.frames_detected,
                        box_count=metric.box_count,
                        time_seconds=metric.time_seconds,
                        percentage=metric.percentage,
                    )
                )

            analysis.total_frames = total_source_frames or None
            analysis.duration_seconds = duration_seconds or None
            analysis.processed_frames = total_source_frames
            analysis.progress = 100.0
            analysis.total_detections = sum(detected_frames.values())
            analysis.raw_detections = total_raw_detections
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = utcnow()
            session.commit()

    def _progress(self, processed_frames: int, metadata: VideoMetadata) -> float:
        if metadata.total_frames > 0:
            return round(min(99.0, (processed_frames / metadata.total_frames) * 100.0), 2)
        if metadata.duration_seconds > 0:
            elapsed = processed_frames / metadata.fps
            return round(min(99.0, (elapsed / metadata.duration_seconds) * 100.0), 2)
        return 0.0

    def _mark_failed(self, analysis_id: int, exc: Exception) -> None:
        try:
            with self._session_factory() as session:
                analysis = session.get(Analysis, analysis_id)
                if analysis is None:
                    return
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = str(exc)[:2000] or exc.__class__.__name__
                analysis.completed_at = utcnow()
                session.commit()
        except Exception:
            logger.exception("No se pudo registrar el error del análisis %s", analysis_id)

    def _clear_preview(self, analysis_id: int) -> None:
        if self._preview_dir is None:
            return
        shutil.rmtree(self._preview_dir / str(analysis_id), ignore_errors=True)

    def list_analyses(self, limit: int = 100, offset: int = 0) -> list[AnalysisSummary]:
        with self._session_factory() as session:
            analyses = session.scalars(
                select(Analysis)
                .order_by(Analysis.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).all()
            return [AnalysisSummary.model_validate(analysis) for analysis in analyses]

    def get_analysis(self, analysis_id: int) -> AnalysisDetail:
        with self._session_factory() as session:
            analysis = session.scalar(
                select(Analysis)
                .where(Analysis.id == analysis_id)
                .options(selectinload(Analysis.brand_results))
            )
            if analysis is None:
                raise AnalysisNotFoundError(f"No existe el análisis {analysis_id}")
            return AnalysisDetail.model_validate(analysis)

    def get_progress(self, analysis_id: int) -> AnalysisProgress:
        with self._session_factory() as session:
            analysis = session.get(Analysis, analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError(f"No existe el análisis {analysis_id}")
            return AnalysisProgress.model_validate(analysis)

    def get_preview(self, analysis_id: int) -> PreviewResult:
        with self._session_factory() as session:
            analysis = session.get(Analysis, analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError(f"No existe el análisis {analysis_id}")
            fps = float(analysis.fps or 0.0)

        frames: list[PreviewFrame] = []
        if self._preview_dir is not None:
            directory = self._preview_dir / str(analysis_id)
            if directory.is_dir():
                for path in sorted(directory.glob("frame_*.jpg")):
                    match = re.fullmatch(r"frame_(\d+)\.jpg", path.name)
                    if match is None:
                        continue
                    frame_index = int(match.group(1))
                    frames.append(
                        PreviewFrame(
                            index=frame_index,
                            timestamp_seconds=(
                                round(frame_index / fps, 3) if fps > 0 else 0.0
                            ),
                            url=f"/analyses/{analysis_id}/preview/frames/{path.name}",
                        )
                    )

        return PreviewResult(
            analysis_id=analysis_id,
            slow_motion_fps=self._preview_slow_motion_fps,
            frames=frames,
        )

    def get_dashboard(self) -> DashboardStats:
        with self._session_factory() as session:
            total_analyses = session.scalar(select(func.count(Analysis.id))) or 0
            completed_filter = Analysis.status == AnalysisStatus.COMPLETED.value
            completed_analyses = (
                session.scalar(select(func.count(Analysis.id)).where(completed_filter)) or 0
            )
            total_detections = (
                session.scalar(
                    select(func.coalesce(func.sum(Analysis.total_detections), 0)).where(
                        completed_filter
                    )
                )
                or 0
            )
            total_video_seconds = float(
                session.scalar(
                    select(func.coalesce(func.sum(Analysis.duration_seconds), 0.0)).where(
                        completed_filter
                    )
                )
                or 0.0
            )

            rows = session.execute(
                select(
                    BrandResult.brand_name,
                    func.sum(BrandResult.frames_detected),
                    func.sum(BrandResult.box_count),
                    func.sum(BrandResult.time_seconds),
                    func.count(func.distinct(BrandResult.analysis_id)),
                )
                .join(Analysis, Analysis.id == BrandResult.analysis_id)
                .where(completed_filter)
                .group_by(BrandResult.brand_name)
            ).all()

            summary_by_name: dict[str, DashboardBrandSummary] = {}
            for brand_name, frames, boxes, seconds, analyses_with_brand in rows:
                total_seconds = float(seconds or 0.0)
                percentage = (
                    (total_seconds / total_video_seconds) * 100.0
                    if total_video_seconds > 0
                    else 0.0
                )
                summary_by_name[brand_name] = DashboardBrandSummary(
                    brand_name=brand_name,
                    total_time_seconds=round(total_seconds, 3),
                    total_frames_detected=int(frames or 0),
                    total_boxes=int(boxes or 0),
                    analyses_with_brand=int(analyses_with_brand or 0),
                    average_percentage=round(max(0.0, min(100.0, percentage)), 2),
                )

            detector = self._detector_provider()
            if detector is not None:
                for brand_name in detector.class_names:
                    summary_by_name.setdefault(
                        brand_name,
                        DashboardBrandSummary(
                            brand_name=brand_name,
                            total_time_seconds=0.0,
                            total_frames_detected=0,
                            total_boxes=0,
                            analyses_with_brand=0,
                            average_percentage=0.0,
                        ),
                    )

            recent = session.scalars(
                select(Analysis).order_by(Analysis.created_at.desc()).limit(5)
            ).all()

            return DashboardStats(
                total_analyses=total_analyses,
                completed_analyses=completed_analyses,
                total_detections=total_detections,
                total_video_seconds=round(total_video_seconds, 3),
                brand_summary=sorted(
                    summary_by_name.values(), key=lambda item: item.total_time_seconds, reverse=True
                ),
                recent_analyses=[AnalysisSummary.model_validate(analysis) for analysis in recent],
            )
