"""Comprobacion del estado del backend."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from app.api.deps import get_app_settings, get_detector
from app.core.config import Settings
from app.schemas.analysis import HealthResponse
from app.services.detector import BrandDetector

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    detector: BrandDetector | None = Depends(get_detector),
) -> HealthResponse:
    database_status = "ok"
    try:
        with request.app.state.session_factory() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        database_status = f"error: {exc}"

    detail = request.app.state.detector_error
    return HealthResponse(
        status="ok" if database_status == "ok" else "degraded",
        app=settings.app_name,
        version=settings.api_version,
        database=database_status,
        model_loaded=detector is not None,
        model_path=str(settings.model_file),
        classes=detector.class_names if detector is not None else [],
        detail=detail,
    )
