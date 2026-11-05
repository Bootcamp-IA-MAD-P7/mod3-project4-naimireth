"""Contratos Pydantic de la API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BrandResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand_name: str
    frames_detected: int
    box_count: int
    time_seconds: float
    percentage: float


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_name: str
    source_type: str
    status: AnalysisStatus
    progress: float
    duration_seconds: float | None
    total_detections: int
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AnalysisStatus
    progress: float
    processed_frames: int
    total_frames: int | None
    error_message: str | None = None


class AnalysisDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_name: str
    source_type: str
    source_reference: str | None
    status: AnalysisStatus
    progress: float
    error_message: str | None
    duration_seconds: float | None
    fps: float | None
    total_frames: int | None
    processed_frames: int
    sampling_stride: int | None
    effective_fps: float | None
    width: int | None
    height: int | None
    total_detections: int
    raw_detections: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    brand_results: list[BrandResultOut] = Field(default_factory=list)


class PreviewFrame(BaseModel):
    index: int
    timestamp_seconds: float
    url: str


class PreviewResult(BaseModel):
    analysis_id: int
    slow_motion_fps: float
    frames: list[PreviewFrame]


class DashboardBrandSummary(BaseModel):
    brand_name: str
    total_time_seconds: float
    total_frames_detected: int
    total_boxes: int
    analyses_with_brand: int
    average_percentage: float


class DashboardStats(BaseModel):
    total_analyses: int
    completed_analyses: int
    total_detections: int
    total_video_seconds: float
    brand_summary: list[DashboardBrandSummary]
    recent_analyses: list[AnalysisSummary]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
    model_loaded: bool
    model_path: str
    classes: list[str]
    detail: str | None = None
