"""Calculo de exposicion publicitaria a partir de fotogramas detectados."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandMetric:
    brand_name: str
    frames_detected: int
    box_count: int
    time_seconds: float
    percentage: float


def compute_brand_metrics(
    detected_frames: dict[str, int],
    box_counts: dict[str, int],
    duration_seconds: float,
    effective_fps: float,
    brand_names: list[str],
) -> list[BrandMetric]:
    """Calcula tiempo y porcentaje estimados.

    Cada marca cuenta como maximo una vez por fotograma muestreado. El tiempo
    se estima dividiendo los fotogramas con presencia entre el FPS efectivo
    del muestreo y se limita a la duracion total del video.
    """

    duration = max(0.0, float(duration_seconds))
    fps = float(effective_fps) if effective_fps > 0 else 1.0
    metrics: list[BrandMetric] = []

    for brand_name in brand_names:
        frames_detected = max(0, int(detected_frames.get(brand_name, 0)))
        box_count = max(0, int(box_counts.get(brand_name, 0)))
        time_seconds = frames_detected / fps

        if duration > 0:
            time_seconds = min(time_seconds, duration)
            percentage = (time_seconds / duration) * 100.0
        else:
            percentage = 0.0

        metrics.append(
            BrandMetric(
                brand_name=brand_name,
                frames_detected=frames_detected,
                box_count=box_count,
                time_seconds=round(time_seconds, 3),
                percentage=round(max(0.0, min(100.0, percentage)), 2),
            )
        )

    return metrics
