from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models_resume import ResumeTask
from app.repositories.resume_task_repository import ResumeTaskRepository
from schemas.resume_api import TaskStatus


def test_resume_task_status_transition():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(bind=engine)
    repo = ResumeTaskRepository()

    task = ResumeTask(
        task_id="t1",
        user_id=1,
        file_name="resume.pdf",
        original_file_name="resume.pdf",
        file_size=10,
        content_type="application/pdf",
        status=TaskStatus.PROCESSING.value,
        start_time=datetime.utcnow(),
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow(),
        delete_flag=0,
    )
    repo.create(db, task)
    repo.update_status(db, "t1", TaskStatus.ANALYZING)
    repo.complete(db, "t1", 99)

    refreshed = repo.get_by_task_id(db, "t1")
    assert refreshed.status == TaskStatus.COMPLETED.value
    assert refreshed.resume_id == 99
    assert refreshed.complete_time is not None
