from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from schemas.cv_models import CvBO, OptimizationRecord


class TaskStatus(str, Enum):
    PROCESSING = "PROCESSING"
    ANALYZING = "ANALYZING"
    SAVING = "SAVING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CvType(str, Enum):
    UPLOAD = "upload"
    EXCELLENT = "excellent"


class ResumeUploadResponse(BaseModel):
    success: bool = True
    taskId: str | None = None
    fileName: str | None = None
    originalFileName: str | None = None
    errorMessage: str | None = None
    message: str | None = "文件上传成功，正在后台处理"
    timestamp: int | None = None


class TaskStatusResponse(BaseModel):
    taskId: str
    status: TaskStatus
    statusMessage: str
    progress: int
    startTime: datetime | None = None
    completeTime: datetime | None = None
    resumeId: str | None = None
    errorMessage: str | None = None
    fileName: str | None = None
    originalFileName: str | None = None
    estimatedRemainingSeconds: int | None = None


class ResumeOptimizeRequest(BaseModel):
    resumeId: str
    jobDescription: str = Field(min_length=1)


class ResumeOptimizedResponse(BaseModel):
    suggestionText: str | None = None
    optimizedResumeId: int | None = None
    optimizationHistory: list[OptimizationRecord] = Field(default_factory=list)
    optimizedCv: CvBO | None = None


class ResumeGenerateRequest(BaseModel):
    optimizedResumeId: str
    downloadFileType: str = "pdf"


class ResumeDetailResponse(CvBO):
    model_config = ConfigDict(extra="ignore")
    resumeId: str | None = None


class SseEnvelope(BaseModel):
    event: str
    data: Any
