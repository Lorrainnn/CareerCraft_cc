from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.interviews import router as interview_router
from app.api.routes.resumes import router as resume_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(resume_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(interview_router, prefix="/interviews", tags=["interviews"])

