from fastapi import HTTPException

from app.core.errors import ErrorCodes


class ApiException(HTTPException):
    def __init__(self, status_code: int = 500, message: str = "", code: str = ""):
        super().__init__(status_code=status_code, detail={"code": code, "message": message or "Error"})


def not_implemented(message: str = "Not implemented") -> None:
    raise ApiException(status_code=501, message=message, code=ErrorCodes.NOT_IMPLEMENTED.code)

