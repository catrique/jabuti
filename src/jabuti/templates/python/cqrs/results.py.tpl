"""Standard results returned by Commands and Queries."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from app.application.cqrs.errors import ErrorCode

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CommandResult(Generic[T]):
    """Outcome of a Command. Fill only the fields the operation needs."""

    success: bool
    data: T | None = None
    rows: int | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None

    @classmethod
    def ok(cls, data: T | None = None, rows: int | None = None) -> "CommandResult[T]":
        return cls(success=True, data=data, rows=rows)

    @classmethod
    def fail(cls, code: ErrorCode, message: str) -> "CommandResult[T]":
        return cls(success=False, error_code=code, error_message=message)


@dataclass(frozen=True, slots=True)
class QueryResult(Generic[T]):
    """Outcome of a Query.

    ``total_rows`` is only meaningful for listings (for example, the total
    before pagination); single-item reads leave it as ``None``.
    """

    data: T | None = None
    total_rows: int | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None

    @property
    def success(self) -> bool:
        return self.error_code is None

    @classmethod
    def ok(cls, data: T, total_rows: int | None = None) -> "QueryResult[T]":
        return cls(data=data, total_rows=total_rows)

    @classmethod
    def fail(cls, code: ErrorCode, message: str) -> "QueryResult[T]":
        return cls(error_code=code, error_message=message)
