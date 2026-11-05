from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def build_settings(tmp_path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        upload_dir=(tmp_path / "uploads").as_posix(),
        output_dir=(tmp_path / "outputs").as_posix(),
        model_preload=False,
    )


def test_health_reports_database_and_missing_model(tmp_path):
    app = create_app(settings=build_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["model_loaded"] is False
    assert payload["classes"] == []


def test_root_endpoint_exposes_docs_and_health(tmp_path):
    app = create_app(settings=build_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"
