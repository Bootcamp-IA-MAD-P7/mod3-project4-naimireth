"""Punto de entrada de la API de Brand Pulse."""

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyses, dashboard, health
from app.core.config import Settings, get_settings
from app.database.db import build_engine, build_session_factory, init_db
from app.services.analysis_service import AnalysisService
from app.services.detector import BrandDetector

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, detector: BrandDetector | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.ensure_directories()

    engine = build_engine(settings)
    init_db(engine)
    session_factory = build_session_factory(engine)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="brand-pulse")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.detector is None and settings.model_preload:
            try:
                app.state.detector = BrandDetector(
                    model_path=settings.model_file,
                    confidence_threshold=settings.model_confidence_threshold,
                    iou_threshold=settings.model_iou_threshold,
                    device=settings.device,
                )
                logger.info("Modelo YOLO cargado desde %s", settings.model_file)
            except Exception as exc:
                app.state.detector_error = str(exc)
                logger.error("No se pudo cargar el modelo: %s", exc)
        yield
        executor.shutdown(wait=False, cancel_futures=True)
        engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        description="Deteccion de marcas patrocinadoras en video y calculo de exposicion.",
        version=settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.executor = executor
    app.state.detector = detector
    app.state.detector_error = None
    app.state.analysis_service = AnalysisService(
        session_factory=session_factory,
        executor=executor,
        detector_provider=lambda: app.state.detector,
        preview_dir=settings.output_path,
        preview_enabled=settings.preview_enabled,
        preview_max_frames=settings.preview_max_frames,
        preview_slow_motion_fps=settings.preview_slow_motion_fps,
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(analyses.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
