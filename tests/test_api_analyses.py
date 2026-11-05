import time

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.detector import DetectedBox


class FakeDetector:
    def __init__(self) -> None:
        self.names = {0: "Adidas", 1: "Emirates", 2: "Nike", 3: "Spotify"}

    @property
    def class_names(self) -> list[str]:
        return [self.names[class_id] for class_id in sorted(self.names)]

    def detect(self, frame: np.ndarray) -> list[DetectedBox]:
        return [
            DetectedBox(0, "Adidas", 0.9, 1.0, 1.0, 20.0, 20.0),
            DetectedBox(2, "Nike", 0.8, 30.0, 30.0, 50.0, 50.0),
        ]


def build_settings(tmp_path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        upload_dir=(tmp_path / "uploads").as_posix(),
        output_dir=(tmp_path / "outputs").as_posix(),
        model_preload=False,
        video_fps_sampling=5,
        video_max_duration_seconds=60,
        video_max_upload_mb=10,
    )


def create_synthetic_video(path, frames=20, fps=10):
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (160, 120),
    )
    if not writer.isOpened():
        pytest.skip("OpenCV no puede escribir MP4 en este entorno")

    for index in range(frames):
        frame = np.full((120, 160, 3), (index * 8) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_full_upload_analysis_flow(tmp_path):
    video_path = tmp_path / "sample.mp4"
    create_synthetic_video(video_path)

    app = create_app(settings=build_settings(tmp_path), detector=FakeDetector())

    with TestClient(app) as client:
        with video_path.open("rb") as handle:
            response = client.post(
                "/api/analyses",
                files={"file": ("sample.mp4", handle, "video/mp4")},
            )

        assert response.status_code == 202
        created = response.json()
        analysis_id = created["id"]
        assert created["status"] in {"queued", "processing", "completed"}

        detail = None
        for _ in range(100):
            detail_response = client.get(f"/api/analyses/{analysis_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()
            if detail["status"] in {"completed", "failed"}:
                break
            time.sleep(0.1)

        assert detail is not None
        assert detail["status"] == "completed", detail.get("error_message")
        assert detail["duration_seconds"] == pytest.approx(2.0, abs=0.05)
        assert detail["processed_frames"] == 20
        assert detail["total_detections"] == 20
        assert detail["raw_detections"] == 20
        assert len(detail["brand_results"]) == 4

        brands = {brand["brand_name"]: brand for brand in detail["brand_results"]}
        assert brands["Adidas"]["frames_detected"] == 10
        assert brands["Adidas"]["time_seconds"] == pytest.approx(2.0, abs=0.05)
        assert brands["Adidas"]["percentage"] == pytest.approx(100.0, abs=0.1)
        assert brands["Emirates"]["frames_detected"] == 0
        assert brands["Nike"]["frames_detected"] == 10

        progress = client.get(f"/api/analyses/{analysis_id}/progress").json()
        assert progress["status"] == "completed"
        assert progress["progress"] == 100.0

        preview = client.get(f"/api/analyses/{analysis_id}/preview")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["analysis_id"] == analysis_id
        assert preview_payload["slow_motion_fps"] == pytest.approx(1.0)
        assert len(preview_payload["frames"]) == 10
        first_frame = preview_payload["frames"][0]
        assert first_frame["index"] == 0
        assert first_frame["timestamp_seconds"] == pytest.approx(0.0)
        frame_response = client.get(f"/api{first_frame['url']}")
        assert frame_response.status_code == 200
        assert frame_response.headers["content-type"].startswith("image/jpeg")

        history = client.get("/api/analyses").json()
        assert len(history) == 1
        assert history[0]["id"] == analysis_id

        dashboard = client.get("/api/dashboard").json()
        assert dashboard["total_analyses"] == 1
        assert dashboard["completed_analyses"] == 1
        assert dashboard["total_detections"] == 20
        assert len(dashboard["brand_summary"]) == 4
        summary = {item["brand_name"]: item for item in dashboard["brand_summary"]}
        assert summary["Adidas"]["average_percentage"] == pytest.approx(100.0, abs=0.1)
        assert summary["Adidas"]["analyses_with_brand"] == 1
        assert summary["Spotify"]["average_percentage"] == 0.0

    time.sleep(0.2)
    assert list(build_settings(tmp_path).upload_path.iterdir()) == []


def test_rejects_non_mp4_file(tmp_path):
    app = create_app(settings=build_settings(tmp_path), detector=FakeDetector())

    with TestClient(app) as client:
        response = client.post(
            "/api/analyses",
            files={"file": ("notes.txt", b"not a video", "text/plain")},
        )

    assert response.status_code == 400
    assert "MP4" in response.json()["detail"]
