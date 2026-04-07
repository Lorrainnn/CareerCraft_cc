from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = "操作成功"
    data: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def success_response(cls, data: T, message: str = "操作成功") -> "ApiResponse[T]":
        return cls(success=True, message=message, data=data, error=None)

    @classmethod
    def error_response(cls, error: str, message: Optional[str] = None) -> "ApiResponse[T]":
        return cls(success=False, message=message, data=None, error=error)

