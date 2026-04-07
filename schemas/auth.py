from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度必须在3-20个字符之间")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 6:
            raise ValueError("密码长度不能小于6位")
        return v


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirmPassword: str
    email: Optional[str] = None

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度必须在3-20个字符之间")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 6:
            raise ValueError("密码长度不能小于6位")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("confirmPassword")
    @classmethod
    def _validate_confirm_password(cls, v: str, info) -> str:
        # cross-field check in later validator
        if not v:
            raise ValueError("确认密码不能为空")
        return v

    def model_post_init(self, __context) -> None:
        # cross-field validation
        if self.password != self.confirmPassword:
            raise ValueError("两次输入的密码不一致")

class SendForgetPasswordCodeRequest(BaseModel):
    username: str
    email: str

    @field_validator("username", "email")
    @classmethod
    def _validate_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("请求参数不能为空")
        return str(v).strip()


class ForgetPasswordRequest(BaseModel):
    username: str
    email: str
    code: str
    newPassword: str

    @field_validator("username", "email", "code", "newPassword")
    @classmethod
    def _validate_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("请求参数不能为空")
        return str(v).strip()


class SecureLoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int


class UserInfoResponse(BaseModel):
    userId: int
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None

