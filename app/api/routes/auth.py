from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import AuthService
from schemas.auth import (
    ForgetPasswordRequest,
    LoginRequest,
    RegisterRequest,
    SecureLoginResponse,
    SendForgetPasswordCodeRequest,
    UserInfoResponse,
)

router = APIRouter()


def get_auth_service() -> AuthService:
    # Lightweight singleton-like service (stateless aside from clients)
    return AuthService()


@router.post("/login", response_model=SecureLoginResponse)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
):
    service = get_auth_service()
    user_id = service.authenticate_user(db, req)
    if user_id is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Generate access token
    token = service.jwt_util.generate_access_token(user_id, req.username)
    return SecureLoginResponse(
        accessToken=token,
        expiresIn=int(service.settings.jwt_access_token_expiration),
    )


@router.post("/register")
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    service = get_auth_service()
    service.register(db, req)
    return {"success": True}


@router.post("/sendForgetPasswordCode")
def send_forget_password_code(
    req: SendForgetPasswordCodeRequest,
    db: Session = Depends(get_db),
):
    service = get_auth_service()
    service.send_forget_password_code(db, req)
    return {"success": True}


@router.post("/forgetPassword")
def forget_password(
    req: ForgetPasswordRequest,
    db: Session = Depends(get_db),
):
    service = get_auth_service()
    service.forget_password(db, req)
    return {"success": True}


@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="无效的token格式")
    token = authorization.removeprefix("Bearer ").strip()
    service = get_auth_service()
    service.logout(token)
    return {"success": True}


@router.get("/validate")
def validate_token(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="用户未登录")
    return {"success": True}


@router.get("/me", response_model=UserInfoResponse)
def me(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="用户未登录")

    service = get_auth_service()
    user = service.get_user_info(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="用户信息不存在")

    return UserInfoResponse(
        userId=int(user.id),
        username=user.username,
        phone=user.phone,
        email=user.email,
    )
