"""Rutas para subir videos y consultar analisis."""

import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_analysis_service, get_app_settings, get_detector
from app.core.config import Settings
from app.schemas.analysis import (
    AnalysisDetail,
    AnalysisProgress,
    AnalysisSummary,
    PreviewResult,
)
from app.services.analysis_service import AnalysisNotFoundError, AnalysisService
from app.services.detector import BrandDetector
from app.services.video_processor import VideoValidationError, inspect_video

router = APIRouter(prefix="/analyses", tags=["analyses"])

CHUNK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {".mp4"}


def _save_upload(file: UploadFile, destination: Path, max_bytes: int) -> int:
    size = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"El vídeo supera el límite de {max_bytes // (1024 * 1024)} MB",
                    )
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )
    return size


@router.post("", response_model=AnalysisDetail, status_code=status.HTTP_202_ACCEPTED)
def create_analysis(
    file: UploadFile = File(...),
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_app_settings),
    detector: BrandDetector | None = Depends(get_detector),
) -> AnalysisDetail:
    if detector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El modelo YOLO no está cargado. Comprueba "
                "models/football_brands/best.pt y reinicia el backend."
            ),
        )

    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no admitido. Sube un archivo MP4.",
        )

    destination = settings.upload_path / f"{uuid4().hex}.mp4"
    max_bytes = settings.video_max_upload_mb * 1024 * 1024
    _save_upload(file, destination, max_bytes)

    try:
        metadata = inspect_video(destination, settings.video_fps_sampling)
    except VideoValidationError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el vídeo: {exc}",
        ) from exc

    if (
        settings.video_max_duration_seconds > 0
        and metadata.duration_seconds > settings.video_max_duration_seconds
    ):
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El vídeo supera la duración máxima permitida de "
                f"{settings.video_max_duration_seconds} segundos"
            ),
        )

    analysis_id = service.create_analysis(
        video_name=filename,
        source_reference=filename,
        metadata=metadata,
    )
    service.submit(analysis_id, destination, metadata)
    return service.get_analysis(analysis_id)


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: AnalysisService = Depends(get_analysis_service),
) -> list[AnalysisSummary]:
    return service.list_analyses(limit=limit, offset=offset)


@router.get("/{analysis_id}/progress", response_model=AnalysisProgress)
def get_progress(
    analysis_id: int,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisProgress:
    try:
        return service.get_progress(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{analysis_id}/preview", response_model=PreviewResult)
def get_preview(
    analysis_id: int,
    service: AnalysisService = Depends(get_analysis_service),
) -> PreviewResult:
    try:
        return service.get_preview(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{analysis_id}/preview/frames/{filename}")
def get_preview_frame(
    analysis_id: int,
    filename: str,
    settings: Settings = Depends(get_app_settings),
) -> FileResponse:
    if re.fullmatch(r"frame_\d{8}\.jpg", filename) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fotograma no encontrado",
        )

    path = settings.output_path / str(analysis_id) / filename
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fotograma no encontrado",
        )
    return FileResponse(path, media_type="image/jpeg")


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(
    analysis_id: int,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisDetail:
    try:
        return service.get_analysis(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
