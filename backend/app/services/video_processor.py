"""Inspeccion y lectura de fotogramas con OpenCV."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np


class VideoValidationError(Exception):
    """El archivo no es un vídeo válido o no se puede procesar."""


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: float
    fps: float
    total_frames: int
    width: int
    height: int
    sampling_stride: int
    effective_fps: float
    expected_samples: int


def inspect_video(file_path: str | Path, target_fps: float) -> VideoMetadata:
    if target_fps <= 0:
        raise VideoValidationError("La frecuencia de muestreo debe ser mayor que cero")

    capture = cv2.VideoCapture(str(file_path))
    try:
        if not capture.isOpened():
            raise VideoValidationError("OpenCV no pudo abrir el vídeo")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if not math.isfinite(fps) or fps <= 0:
            fps = 25.0

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = total_frames / fps if total_frames > 0 else 0.0
        stride = max(1, int(round(fps / target_fps)))
        effective_fps = fps / stride
        expected_samples = math.ceil(total_frames / stride) if total_frames > 0 else 0

        return VideoMetadata(
            duration_seconds=duration,
            fps=fps,
            total_frames=total_frames,
            width=width,
            height=height,
            sampling_stride=stride,
            effective_fps=effective_fps,
            expected_samples=expected_samples,
        )
    finally:
        capture.release()


def iter_sampled_frames(file_path: str | Path, stride: int) -> Iterator[tuple[int, np.ndarray]]:
    capture = cv2.VideoCapture(str(file_path))
    try:
        if not capture.isOpened():
            raise VideoValidationError("OpenCV no pudo abrir el vídeo")

        index = 0
        while True:
            if not capture.grab():
                break
            if index % stride == 0:
                ok, frame = capture.retrieve()
                if not ok:
                    break
                yield index, frame
            index += 1
    finally:
        capture.release()
