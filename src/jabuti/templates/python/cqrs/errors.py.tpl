"""Application error codes, independent of HTTP or any framework."""

from enum import Enum


class ErrorCode(str, Enum):
    """Why an operation failed, as seen by the application."""

    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    BAD_GATEWAY = "BAD_GATEWAY"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApplicationError(Exception):
    """A known failure raised by an operation, kept with its error code.

    Raise it from ``execute()`` when the caller must be able to tell the
    failure apart (for example ``NOT_FOUND`` or ``CONFLICT``). The handlers
    turn it into a failed result instead of an ``INTERNAL_ERROR``.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
