from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCode:
    code: str
    message: str


class ErrorCodes:
    UNAUTHORIZED = ErrorCode("UNAUTHORIZED", "Unauthorized")
    FORBIDDEN = ErrorCode("FORBIDDEN", "Forbidden")
    BAD_REQUEST = ErrorCode("BAD_REQUEST", "Bad request")
    NOT_FOUND = ErrorCode("NOT_FOUND", "Not found")
    INTERNAL = ErrorCode("INTERNAL_ERROR", "Internal error")
    NOT_IMPLEMENTED = ErrorCode("NOT_IMPLEMENTED", "Not implemented")

