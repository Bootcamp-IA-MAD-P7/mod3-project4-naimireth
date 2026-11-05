"""Configuracion central de la aplicacion."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Ajustes leidos de variables de entorno y del archivo .env."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Brand Pulse API"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "0.1.0"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///backend/data/brand_pulse.db"
    database_echo: bool = False

    model_path: str = "models/football_brands/best.pt"
    model_preload: bool = True
    model_confidence_threshold: float = 0.25
    model_iou_threshold: float = 0.45
    device: str = "cpu"

    video_fps_sampling: float = 2.0
    video_max_duration_seconds: int = 1800
    video_max_upload_mb: int = 2048
    frame_save_enabled: bool = False

    upload_dir: str = "backend/storage/uploads"
    output_dir: str = "backend/storage/outputs"
    preview_enabled: bool = True
    preview_max_frames: int = 240
    preview_slow_motion_fps: float = 1.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (REPO_ROOT / path).resolve()

    @property
    def model_file(self) -> Path:
        return self.resolve_path(self.model_path)

    @property
    def upload_path(self) -> Path:
        return self.resolve_path(self.upload_dir)

    @property
    def output_path(self) -> Path:
        return self.resolve_path(self.output_dir)

    @property
    def sqlalchemy_url(self) -> str:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return self.database_url

        raw_path = self.database_url[len(prefix) :]
        if raw_path == ":memory:" or raw_path.startswith("file:"):
            return self.database_url

        path = Path(raw_path)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        return f"{prefix}{path.as_posix()}"

    def ensure_directories(self) -> None:
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)

        url = self.sqlalchemy_url
        prefix = "sqlite:///"
        if url.startswith(prefix):
            database_file = Path(url[len(prefix) :])
            if database_file.name not in {"", ":memory:"}:
                database_file.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
