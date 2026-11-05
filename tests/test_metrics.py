from app.services.metrics import compute_brand_metrics


def test_compute_metrics_uses_effective_fps_and_preserves_brand_order():
    metrics = compute_brand_metrics(
        detected_frames={"Adidas": 10, "Nike": 3},
        box_counts={"Adidas": 14, "Nike": 3},
        duration_seconds=20.0,
        effective_fps=2.0,
        brand_names=["Adidas", "Emirates", "Nike", "Spotify"],
    )

    assert [metric.brand_name for metric in metrics] == ["Adidas", "Emirates", "Nike", "Spotify"]
    assert metrics[0].time_seconds == 5.0
    assert metrics[0].percentage == 25.0
    assert metrics[0].frames_detected == 10
    assert metrics[0].box_count == 14
    assert metrics[2].time_seconds == 1.5
    assert metrics[2].percentage == 7.5
    assert metrics[1].time_seconds == 0.0
    assert metrics[3].percentage == 0.0


def test_compute_metrics_caps_time_at_video_duration():
    metrics = compute_brand_metrics(
        detected_frames={"Adidas": 30},
        box_counts={"Adidas": 30},
        duration_seconds=10.0,
        effective_fps=2.0,
        brand_names=["Adidas"],
    )

    assert metrics[0].time_seconds == 10.0
    assert metrics[0].percentage == 100.0


def test_compute_metrics_without_duration_returns_zero_percentage():
    metrics = compute_brand_metrics(
        detected_frames={"Spotify": 4},
        box_counts={"Spotify": 4},
        duration_seconds=0.0,
        effective_fps=2.0,
        brand_names=["Spotify"],
    )

    assert metrics[0].time_seconds == 2.0
    assert metrics[0].percentage == 0.0
