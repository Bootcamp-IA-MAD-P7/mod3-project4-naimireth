"""Carga y ejecucion del modelo YOLO entrenado."""

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import numpy as np


@dataclass(frozen=True)
class DetectedBox:
    class_id: int
    brand_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class BrandDetector:
    """Envoltorio del modelo que se instancia una sola vez por proceso."""

    def __init__(
        self,
        model_path: str | Path,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "cpu",
    ) -> None:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el modelo en {path}")

        from ultralytics import YOLO

        self.model_path = path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self._model = YOLO(str(path))
        self._lock = Lock()

        raw_names = getattr(self._model, "names", None) or {}
        self.names = {int(key): str(value) for key, value in raw_names.items()}
        if not self.names:
            raise ValueError("El modelo no expone nombres de clases")

    @property
    def class_names(self) -> list[str]:
        return [self.names[class_id] for class_id in sorted(self.names)]

    def detect(self, frame: np.ndarray) -> list[DetectedBox]:
        with self._lock:
            results = self._model.predict(
                source=frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False,
            )

        if not results:
            return []

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []

        detections: list[DetectedBox] = []
        for class_id, confidence, coordinates in zip(
            boxes.cls.tolist(),
            boxes.conf.tolist(),
            boxes.xyxy.tolist(),
        ):
            brand_name = self.names.get(int(class_id))
            if brand_name is None:
                continue
            x1, y1, x2, y2 = coordinates
            detections.append(
                DetectedBox(
                    class_id=int(class_id),
                    brand_name=brand_name,
                    confidence=float(confidence),
                    x1=float(x1),
                    y1=float(y1),
                    x2=float(x2),
                    y2=float(y2),
                )
            )
        return detections
