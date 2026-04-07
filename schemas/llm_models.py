from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CvReview(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: float
    feedback: str

