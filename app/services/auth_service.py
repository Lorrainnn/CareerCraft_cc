from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Optional

import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.jwt_utils import JwtTokenUtil
from app.integrations.email_sender import send_html_mail
from app.repositories.user_repository import UserRepository

from app.core.settings import get_settings
from app.core.jwt_utils import get_redis_client

from schemas.auth import (  # type: ignore
    ForgetPasswordRequest,
    LoginRequest,
    RegisterRequest,
    SendForgetPasswordCodeRequest,
)


def _hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def _check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


class AuthService:
    def __init__(self) -> None:
        self.jwt_util = JwtTokenUtil()
        self.user_repo = UserRepository()
        self.settings = get_settings()
        self.redis = get_redis_client()

    def authenticate_user(self, db: Session, login: LoginRequest) -> Optional[int]:
        user = self.user_repo.get_by_username(db, login.username)
        if user is None:
            return None
        if not _check_password(login.password, user.password):
            return None
        # status: 1-normal, 0-disabled
        if user.status is not None and int(user.status) != 1:
            return None
        self.user_repo.update_last_login_time(db, int(user.id))
        return int(user.id)

    def logout(self, token: str) -> None:
        if not token:
            return
        try:
            self.jwt_util.add_token_to_blacklist(token)
        except Exception:
            # Keep logout idempotent.
            return

    def get_user_info(self, db: Session, user_id: int):
        return self.user_repo.get_by_id(db, user_id)

    def register(self, db: Session, req: RegisterRequest) -> None:
        # check username
        if self.user_repo.count_by_username(db, req.username) > 0:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # check email if provided
        if req.email:
            if self.user_repo.count_by_email(db, req.email) > 0:
                raise HTTPException(status_code=400, detail="邮箱已被注册")

        password_hash = _hash_password(req.password)
        self.user_repo.create_user(db, req.username, password_hash, req.email)

    def send_forget_password_code(self, db: Session, req: SendForgetPasswordCodeRequest) -> None:
        user = self.user_repo.get_by_username_and_email(db, req.username, req.email)
        if user is None:
            raise HTTPException(status_code=400, detail="用户名或注册邮箱错误")

        code = "".join(secrets.choice("0123456789") for _ in range(6))
        redis_key = f"forget_password_code:{req.username}"

        # 5 minutes
        self.redis.set(redis_key, code, ex=5 * 60)

        subject = "【JobSpark】找回密码验证码"
        content = (
            f"尊敬的用户 {req.username}：<br/><br/>"
            f"您正在申请找回密码，您的验证码为：<b>{code}</b><br/><br/>"
            f"该验证码5分钟内有效，请勿泄露给他人。"
        )
        try:
            ok = send_html_mail(req.email, subject, content)
        except Exception as e:
            ok = False
            # 发送失败时删除验证码，避免用户拿着失效状态继续重试
            self.redis.delete(redis_key)
            raise HTTPException(status_code=500, detail="验证码发送失败，请检查邮箱地址或稍后重试") from e

        if not ok:
            self.redis.delete(redis_key)
            raise HTTPException(status_code=500, detail="验证码发送失败，请检查邮箱地址或稍后重试")

    def forget_password(self, db: Session, req: ForgetPasswordRequest) -> None:
        user = self.user_repo.get_by_username_and_email(db, req.username, req.email)
        if user is None:
            raise HTTPException(status_code=400, detail="用户名或注册邮箱错误")

        redis_key = f"forget_password_code:{req.username}"
        cached_code = self.redis.get(redis_key)
        if not cached_code or str(cached_code) != req.code:
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        new_hash = _hash_password(req.newPassword)
        ok = self.user_repo.update_password(db, user, new_hash)
        if not ok:
            raise HTTPException(status_code=500, detail="重置密码失败，请稍后重试")

        self.redis.delete(redis_key)
