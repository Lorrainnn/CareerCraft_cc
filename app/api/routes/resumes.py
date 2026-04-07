import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.progress_stream import progress_broker
from app.services.resume_service import resume_service
from schemas.resume_api import ResumeGenerateRequest, ResumeOptimizeRequest

router = APIRouter()


@router.get("/list")
def list_resumes(request: Request, cv_type: str | None = None, db: Session = Depends(get_db)):
    return resume_service.list_resumes(db, user_id=request.state.user_id, cv_type=cv_type)


@router.get("/{resume_id}")
def get_resume(resume_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        return resume_service.get_resume(db, user_id=request.state.user_id, resume_id=int(resume_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/upload")
def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    cvType: str = Form("upload"),
    db: Session = Depends(get_db),
):
    return resume_service.upload_resume(db, user_id=request.state.user_id, file=file, cv_type=cvType)


@router.post("/optimize")
def optimize_resume(
    payload: ResumeOptimizeRequest, request: Request, db: Session = Depends(get_db)
):
    try:
        return resume_service.optimize_resume(db, user_id=request.state.user_id, request=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/optimize/stream")
async def stream_optimize_resume(
    payload: ResumeOptimizeRequest, request: Request, db: Session = Depends(get_db)
):
    try:
        stream_id, task = await resume_service.optimize_resume_stream(
            db, user_id=request.state.user_id, request=payload
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def event_stream():
        try:
            async for chunk in progress_broker.iterator(stream_id):
                if await request.is_disconnected():
                    task.cancel()
                    break
                yield chunk
        finally:
            task.cancel()
            await progress_broker.close(stream_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/generateOptimizedFile")
def generate_optimized_file(
    payload: ResumeGenerateRequest, request: Request, db: Session = Depends(get_db)
):
    data, media_type = resume_service.generate_file(db, user_id=request.state.user_id, request=payload)
    return Response(content=data, media_type=media_type)


@router.get("/task/{task_id}/status")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    try:
        return resume_service.get_task_status(db, task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/task/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    return {"success": resume_service.cancel_task(db, task_id=task_id)}


@router.post("/{resume_id}/embedding")
def store_embedding(resume_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        return {"success": resume_service.store_embedding(db, user_id=request.state.user_id, resume_id=resume_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
