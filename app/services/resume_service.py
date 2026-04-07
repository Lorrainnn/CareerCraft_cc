from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models_resume import ResumeTask
from app.render.template_renderer import TemplateRenderer
from app.repositories.cv_repository import CvRepository
from app.repositories.resume_task_repository import ResumeTaskRepository
from app.services.file_storage_service import FileStorageService
from app.services.llm_service import LlmService
from app.services.optimization_service import OptimizationService
from app.services.pdf_extractor import PdfExtractor
from app.services.progress_stream import progress_broker
from app.services.rag_service import ResumeRagService
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.runtime import optimize_worker_pool, resume_worker_pool
from schemas.cv_models import CvBO
from schemas.resume_api import (
    CvType,
    ResumeDetailResponse,
    ResumeGenerateRequest,
    ResumeOptimizeRequest,
    ResumeOptimizedResponse,
    ResumeUploadResponse,
    TaskStatus,
    TaskStatusResponse,
)


class ResumeService:
    def __init__(self) -> None:
        self.cv_repository = CvRepository()
        self.task_repository = ResumeTaskRepository()
        self.file_storage_service = FileStorageService()
        self.llm_service = LlmService()
        self.pdf_extractor = PdfExtractor()
        self.analysis_service = ResumeAnalysisService(
            self.file_storage_service, self.pdf_extractor, self.llm_service
        )
        self.rag_service = ResumeRagService(self.llm_service)
        self.optimization_service = OptimizationService(self.llm_service, self.rag_service)
        self.renderer = TemplateRenderer()

    def list_resumes(self, db: Session, *, user_id: int, cv_type: str | None) -> list[ResumeDetailResponse]:
        rows = self.cv_repository.get_cv_list(db, user_id=user_id, cv_type=cv_type)
        result: list[ResumeDetailResponse] = []
        for row in rows:
            cv = self.cv_repository.to_cv_bo(db, row)
            result.append(ResumeDetailResponse(resumeId=str(row.id), **cv.model_dump()))
        return result

    def get_resume(self, db: Session, *, user_id: int, resume_id: int) -> ResumeDetailResponse:
        row = self.cv_repository.get_cv(db, user_id=user_id, resume_id=resume_id)
        if not row:
            raise ValueError("简历不存在")
        cv = self.cv_repository.to_cv_bo(db, row)
        return ResumeDetailResponse(resumeId=str(row.id), **cv.model_dump())

    def upload_resume(self, db: Session, *, user_id: int, file: UploadFile, cv_type: str) -> ResumeUploadResponse:
        storage = self.file_storage_service.save_uploaded_file(file)
        task_id = str(uuid.uuid4().int)[:18]
        task = ResumeTask(
            task_id=task_id,
            user_id=user_id,
            file_name=storage.unique_file_name,
            original_file_name=storage.original_file_name,
            file_size=storage.file_size,
            content_type=storage.content_type,
            file_path=storage.file_path,
            status=TaskStatus.PROCESSING.value,
            start_time=datetime.utcnow(),
            create_time=datetime.utcnow(),
            update_time=datetime.utcnow(),
            delete_flag=0,
        )
        self.task_repository.create(db, task)
        resume_worker_pool.submit(self._process_resume_task, task_id, user_id, storage.unique_file_name, cv_type)
        return ResumeUploadResponse(
            success=True,
            taskId=task_id,
            fileName=storage.unique_file_name,
            originalFileName=storage.original_file_name,
            timestamp=int(time.time() * 1000),
        )

    def _process_resume_task(self, task_id: str, user_id: int, file_name: str, cv_type: str) -> None:
        from app.db.session import get_engine
        from sqlalchemy.orm import Session

        engine = get_engine()
        db = Session(bind=engine)
        resume_id: int | None = None
        try:
            self.task_repository.update_status(db, task_id, TaskStatus.ANALYZING)
            cv = self.analysis_service.analyze_resume_file(file_name)
            cv.userId = user_id
            cv.cvType = cv_type
            self.task_repository.update_status(db, task_id, TaskStatus.SAVING)
            resume_id = self.cv_repository.save_cv(db, cv)
            self.task_repository.complete(db, task_id, resume_id)
        except Exception as exc:
            self.task_repository.fail(db, task_id, str(exc), resume_id=resume_id)
        finally:
            db.close()

    def get_task_status(self, db: Session, *, task_id: str) -> TaskStatusResponse:
        task = self.task_repository.get_by_task_id(db, task_id)
        if not task:
            raise ValueError("任务不存在")
        progress_map = {
            TaskStatus.PROCESSING.value: 10,
            TaskStatus.ANALYZING.value: 60,
            TaskStatus.SAVING.value: 90,
            TaskStatus.COMPLETED.value: 100,
            TaskStatus.FAILED.value: 0,
        }
        message_map = {
            TaskStatus.PROCESSING.value: "处理中",
            TaskStatus.ANALYZING.value: "解析中",
            TaskStatus.SAVING.value: "存储中",
            TaskStatus.COMPLETED.value: "完成",
            TaskStatus.FAILED.value: "失败",
        }
        estimated = None
        if task.status != TaskStatus.COMPLETED.value and task.start_time:
            elapsed = max(int((datetime.utcnow() - task.start_time).total_seconds()), 0)
            estimated = max(75 - elapsed, 1)
        return TaskStatusResponse(
            taskId=task.task_id,
            status=task.status,
            statusMessage=message_map.get(task.status, task.status),
            progress=progress_map.get(task.status, 0),
            startTime=task.start_time,
            completeTime=task.complete_time,
            resumeId=str(task.resume_id) if task.resume_id else None,
            errorMessage=task.error_message,
            fileName=task.file_name,
            originalFileName=task.original_file_name,
            estimatedRemainingSeconds=estimated,
        )

    def cancel_task(self, db: Session, *, task_id: str) -> bool:
        task = self.task_repository.fail(db, task_id, "Task cancelled by user")
        return bool(task)

    def store_embedding(self, db: Session, *, user_id: int, resume_id: int) -> bool:
        row = self.cv_repository.get_cv(db, user_id=user_id, resume_id=resume_id)
        if not row:
            raise ValueError("简历不存在")
        cv = self.cv_repository.to_cv_bo(db, row)
        self.rag_service.store_cv(cv, payload={"resume_id": resume_id, "user_id": user_id})
        return True

    def optimize_resume(
        self, db: Session, *, user_id: int, request: ResumeOptimizeRequest
    ) -> ResumeOptimizedResponse:
        row = self.cv_repository.get_cv(
            db, user_id=user_id, resume_id=int(request.resumeId), cv_type=CvType.UPLOAD.value
        )
        if not row:
            raise ValueError("简历不存在，请重新上传简历")
        cv = self.cv_repository.to_cv_bo(db, row)
        optimized_cv = asyncio.run(
            self.optimization_service.optimize(cv=cv, job_description=request.jobDescription)
        )
        optimized_cv.userId = user_id
        optimized_cv.cvType = CvType.UPLOAD.value
        new_resume_id = self.cv_repository.save_cv(db, optimized_cv)
        return ResumeOptimizedResponse(
            suggestionText=optimized_cv.advice,
            optimizedResumeId=new_resume_id,
            optimizationHistory=optimized_cv.optimizationHistory,
            optimizedCv=optimized_cv,
        )

    async def optimize_resume_stream(
        self, db: Session, *, user_id: int, request: ResumeOptimizeRequest
    ) -> tuple[str, asyncio.Task[None]]:
        row = self.cv_repository.get_cv(
            db, user_id=user_id, resume_id=int(request.resumeId), cv_type=CvType.UPLOAD.value
        )
        if not row:
            raise ValueError("简历不存在，请重新上传简历")
        cv = self.cv_repository.to_cv_bo(db, row)
        stream_id, _ = progress_broker.create()

        async def runner() -> None:
            try:
                optimized_cv = await self.optimization_service.optimize(
                    cv=cv, job_description=request.jobDescription, stream_id=stream_id
                )
                optimized_cv.userId = user_id
                optimized_cv.cvType = CvType.UPLOAD.value
                loop = asyncio.get_running_loop()

                def save_with_new_session() -> int:
                    from sqlalchemy.orm import Session

                    from app.db.session import get_engine

                    worker_db = Session(bind=get_engine())
                    try:
                        return self.cv_repository.save_cv(worker_db, optimized_cv)
                    finally:
                        worker_db.close()

                new_resume_id = await loop.run_in_executor(optimize_worker_pool, save_with_new_session)
                await progress_broker.emit(
                    stream_id,
                    "result",
                    ResumeOptimizedResponse(
                        suggestionText=optimized_cv.advice,
                        optimizedResumeId=new_resume_id,
                        optimizationHistory=optimized_cv.optimizationHistory,
                        optimizedCv=optimized_cv,
                    ).model_dump(mode="json"),
                )
            finally:
                await progress_broker.close(stream_id)

        return stream_id, asyncio.create_task(runner())

    def generate_file(self, db: Session, *, user_id: int, request: ResumeGenerateRequest) -> tuple[bytes, str]:
        row = self.cv_repository.get_cv(db, user_id=user_id, resume_id=int(request.optimizedResumeId))
        if not row:
            raise ValueError("简历不存在")
        cv = self.cv_repository.to_cv_bo(db, row)
        markdown = self.renderer.render_markdown(cv)
        html = self.renderer.markdown_to_html(
            markdown,
            two_column=bool(cv.meta and cv.meta.twoColumnLayout),
            show_avatar=bool(cv.meta and cv.meta.showAvatar),
            show_social=bool(cv.meta is None or cv.meta.showSocial),
        )
        file_type = request.downloadFileType.lower()
        if file_type == "html":
            return html.encode("utf-8"), "text/html"
        if file_type == "docx":
            return self.renderer.html_to_docx(html), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return self.renderer.html_to_pdf(html), "application/pdf"


resume_service = ResumeService()
