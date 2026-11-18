"""Query: a read-only operation."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Generic, TypeVar

from app.application.cqrs.results import QueryResult

T = TypeVar("T")


class Query(ABC, Generic[T]):
    """Read application state without intentionally changing it.

    Override ``validate`` or ``has_permission`` only when the operation needs
    them. ``execute`` may be a regular method or ``async def``.
    """

    def validate(self) -> bool:
        return True

    def has_permission(self) -> bool:
        return True

    @abstractmethod
    def execute(self) -> QueryResult[T] | Awaitable[QueryResult[T]]:
        """Read the data and describe the outcome."""
