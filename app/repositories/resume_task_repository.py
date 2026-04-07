from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models_resume import ResumeTask
from schemas.resume_api import TaskStatus


class ResumeTaskRepository:
    def create(self, db: Session, task: ResumeTask) -> ResumeTask:
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_by_task_id(self, db: Session, task_id: str) -> ResumeTask | None:
        stmt = select(ResumeTask).where(ResumeTask.task_id == task_id, ResumeTask.delete_flag == 0)
        return db.execute(stmt).scalar_one_or_none()

    def list_user_tasks(
        self, db: Session, *, user_id: int | None = None, status: str | None = None
    ) -> list[ResumeTask]:
        stmt = select(ResumeTask).where(ResumeTask.delete_flag == 0).order_by(ResumeTask.create_time.desc())
        if user_id is not None:
            stmt = stmt.where(ResumeTask.user_id == user_id)
        if status:
            stmt = stmt.where(ResumeTask.status == status)
        return list(db.execute(stmt).scalars().all())

    def update_status(self, db: Session, task_id: str, status: TaskStatus) -> ResumeTask | None:
        task = self.get_by_task_id(db, task_id)
        if not task:
            return None
        task.status = status.value
        task.update_time = datetime.utcnow()
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def complete(self, db: Session, task_id: str, resume_id: int) -> ResumeTask | None:
        task = self.get_by_task_id(db, task_id)
        if not task:
            return None
        now = datetime.utcnow()
        task.resume_id = resume_id
        task.status = TaskStatus.COMPLETED.value
        task.complete_time = now
        task.update_time = now
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def fail(
        self, db: Session, task_id: str, error_message: str, resume_id: int | None = None
    ) -> ResumeTask | None:
        task = self.get_by_task_id(db, task_id)
        if not task:
            return None
        now = datetime.utcnow()
        task.resume_id = resume_id
        task.status = TaskStatus.FAILED.value
        task.error_message = error_message
        task.complete_time = now
        task.update_time = now
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
