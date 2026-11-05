"""Resumen agregado para el dashboard."""

from fastapi import APIRouter, Depends

from app.api.deps import get_analysis_service
from app.schemas.analysis import DashboardStats
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(
    service: AnalysisService = Depends(get_analysis_service),
) -> DashboardStats:
    return service.get_dashboard()
