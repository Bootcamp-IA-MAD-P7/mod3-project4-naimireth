"""Generacion de fotogramas anotados para la vista previa."""

import logging
import shutil
from pathlib import Path

import cv2
import numpy as np

from app.services.detector import DetectedBox

logger = logging.getLogger(__name__)

BRAND_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "Adidas": (128, 222, 74),
    "Emirates": (53, 230, 163),
    "Nike": (21, 204, 250),
    "Spotify": (191, 212, 45),
}
DEFAULT_COLOR_BGR = (134, 239, 172)
LABEL_COLOR_BGR = (10, 25, 15)


class PreviewWriter:
    """Dibuja cajas de deteccion y guarda fotogramas JPEG."""

    def __init__(self, root: Path, analysis_id: int, max_frames: int = 240) -> None:
        self._root = root
        self._analysis_id = analysis_id
        self._max_frames = max_frames
        self._written = 0

    @property
    def directory(self) -> Path:
        return self._root / str(self._analysis_id)

    def write(
        self,
        frame: np.ndarray,
        detections: list[DetectedBox],
        frame_index: int,
    ) -> None:
        if self._written >= self._max_frames or not detections:
            return

        annotated = frame.copy()
        height, width = annotated.shape[:2]
        thickness = max(2, round(min(height, width) / 320))

        for box in detections:
            color = BRAND_COLORS_BGR.get(box.brand_name, DEFAULT_COLOR_BGR)
            x1 = max(0, min(width - 1, int(round(box.x1))))
            y1 = max(0, min(height - 1, int(round(box.y1))))
            x2 = max(0, min(width - 1, int(round(box.x2))))
            y2 = max(0, min(height - 1, int(round(box.y2))))
            if x2 <= x1 or y2 <= y1:
                continue

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            label = f"{box.brand_name} {box.confidence:.0%}"
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            label_top = y1 - text_height - baseline - 6
            if label_top < 0:
                label_top = y2 + 4
            label_right = min(width - 1, x1 + text_width + 10)
            label_bottom = min(height - 1, label_top + text_height + baseline + 4)

            cv2.rectangle(annotated, (x1, label_top), (label_right, label_bottom), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 5, min(height - 1, label_top + text_height + 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                LABEL_COLOR_BGR,
                1,
                cv2.LINE_AA,
            )

        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"frame_{frame_index:08d}.jpg"
        if cv2.imwrite(
            str(destination),
            annotated,
            [int(cv2.IMWRITE_JPEG_QUALITY), 85],
        ):
            self._written += 1

    def cleanup(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)
