"""Command: an operation that may change application state."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Generic, TypeVar

from app.application.cqrs.results import CommandResult

T = TypeVar("T")


class Command(ABC, Generic[T]):
    """Execute a state-changing use case.

    Override ``validate`` or ``has_permission`` only when the operation needs
    them. ``execute`` may be a regular method or ``async def``.
    """

    def validate(self) -> bool:
        return True

    def has_permission(self) -> bool:
        return True

    @abstractmethod
    def execute(self) -> CommandResult[T] | Awaitable[CommandResult[T]]:
        """Perform the change and describe its outcome."""
