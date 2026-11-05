"""Dependencias compartidas de los routers."""

from fastapi import Request

from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.detector import BrandDetector


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service


def get_detector(request: Request) -> BrandDetector | None:
    return request.app.state.detector
