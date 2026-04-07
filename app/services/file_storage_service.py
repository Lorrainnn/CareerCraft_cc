from __future__ import annotations

import os
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from app.core.settings import get_settings


@dataclass
class StoredFile:
    bucket_name: str
    unique_file_name: str
    original_file_name: str
    file_size: int
    content_type: str | None
    file_path: str


class FileStorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket_name = settings.oss_bucket_name or "jobspark-resume"
        self.base_dir = Path(".oss") / self.bucket_name
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, file: UploadFile, bucket_name: str | None = None) -> StoredFile:
        bucket_name = bucket_name or self.bucket_name
        unique_file_name = self.generate_unique_object_name(file.filename)
        dest = self._resolve_path(bucket_name, unique_file_name)
        dest.parent.mkdir(parents=True, exist_ok=True)

        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)

        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        return StoredFile(
            bucket_name=bucket_name,
            unique_file_name=unique_file_name,
            original_file_name=file.filename or "",
            file_size=size,
            content_type=file.content_type,
            file_path=str(dest),
        )

    def download_file_by_bucket_and_name(self, bucket_name: str | None, file_name: str) -> BinaryIO:
        path = self._resolve_path(bucket_name or self.bucket_name, file_name)
        return path.open("rb")

    def generate_unique_object_name(self, original_name: str | None) -> str:
        suffix = Path(original_name or "").suffix
        year_month = datetime.utcnow().strftime("%Y-%m")
        return f"resumes/{year_month}/{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{suffix}"

    def _resolve_path(self, bucket_name: str, object_name: str) -> Path:
        return Path(".oss") / bucket_name / object_name
