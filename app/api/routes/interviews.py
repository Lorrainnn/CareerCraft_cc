from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.interview_service import InterviewService
from app.services.resume_service import resume_service
from schemas.interview_models import InterviewContinueRequest, InterviewStartRequest

router = APIRouter()
interview_service = InterviewService(resume_service.llm_service)


@router.post("/sessions")
def start_interview(payload: InterviewStartRequest, request: Request, db: Session = Depends(get_db)):
    try:
        resume = resume_service.get_resume(db, user_id=request.state.user_id, resume_id=payload.resumeId)
        return interview_service.start(
            user_id=request.state.user_id,
            resume_id=payload.resumeId,
            job_description=payload.jobDescription,
            cv=resume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/continue")
def continue_interview(session_id: int, payload: InterviewContinueRequest):
    try:
        return interview_service.continue_session(session_id, payload.userAnswer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/status")
def get_session_status(session_id: int):
    try:
        return interview_service.status(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/finish")
def finish_interview(session_id: int):
    try:
        return interview_service.finish(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
