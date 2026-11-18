"""FastAPI adapter: turn application results into HTTP responses."""

from typing import TypeVar

from fastapi import HTTPException, status

from app.application.cqrs import CommandResult, ErrorCode, QueryResult

T = TypeVar("T")

HTTP_STATUS = {
    ErrorCode.INVALID_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
    ErrorCode.BAD_GATEWAY: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def unwrap(result: CommandResult[T] | QueryResult[T]) -> T | None:
    """Return the result data, or raise the HTTPException for its error code."""
    if result.success:
        return result.data
    code = result.error_code or ErrorCode.INTERNAL_ERROR
    raise HTTPException(status_code=HTTP_STATUS[code], detail=result.error_message)
