"""Run Commands and Queries with the checks every operation shares.

Handlers validate, authorize, execute and turn unexpected exceptions into a
generic ``INTERNAL_ERROR``. They never open transactions, commit, publish
events or know about HTTP: that belongs to each operation or to its adapter.
"""

import inspect
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from app.application.cqrs.command import Command
from app.application.cqrs.errors import ApplicationError, ErrorCode
from app.application.cqrs.query import Query
from app.application.cqrs.results import CommandResult, QueryResult

T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)

_INVALID_MESSAGE = "Invalid request."
_FORBIDDEN_MESSAGE = "Permission denied."
_UNEXPECTED_MESSAGE = "Unexpected error."

Operation = Command[Any] | Query[Any]
Failure = Callable[[ErrorCode, str], R]


class CommandHandler:
    """Validate, authorize and execute Commands."""

    def handle(self, command: Command[T]) -> CommandResult[T]:
        """Run a Command whose ``execute`` is synchronous."""
        return _run(command, CommandResult.fail)

    async def handle_async(self, command: Command[T]) -> CommandResult[T]:
        """Run a Command whose ``execute`` is synchronous or ``async``."""
        return await _run_async(command, CommandResult.fail)


class QueryHandler:
    """Validate, authorize and execute Queries."""

    def handle(self, query: Query[T]) -> QueryResult[T]:
        """Run a Query whose ``execute`` is synchronous."""
        return _run(query, QueryResult.fail)

    async def handle_async(self, query: Query[T]) -> QueryResult[T]:
        """Run a Query whose ``execute`` is synchronous or ``async``."""
        return await _run_async(query, QueryResult.fail)


def _run(operation: Operation, fail: Failure[R]) -> R:
    try:
        rejection = _rejection(operation, fail)
        if rejection is not None:
            return rejection
        result = operation.execute()
    except ApplicationError as error:
        return fail(error.code, error.message)
    except Exception:
        return _unexpected(operation, fail)

    if inspect.isawaitable(result):
        if inspect.iscoroutine(result):
            result.close()
        raise TypeError(
            f"{type(operation).__name__}.execute is async; use handle_async()."
        )
    return result


async def _run_async(operation: Operation, fail: Failure[R]) -> R:
    try:
        rejection = _rejection(operation, fail)
        if rejection is not None:
            return rejection
        result = operation.execute()
        if inspect.isawaitable(result):
            result = await result
    except ApplicationError as error:
        return fail(error.code, error.message)
    except Exception:
        return _unexpected(operation, fail)
    return result


def _rejection(operation: Operation, fail: Failure[R]) -> R | None:
    if not operation.validate():
        return fail(ErrorCode.INVALID_REQUEST, _INVALID_MESSAGE)
    if not operation.has_permission():
        return fail(ErrorCode.FORBIDDEN, _FORBIDDEN_MESSAGE)
    return None


def _unexpected(operation: Operation, fail: Failure[R]) -> R:
    # The traceback stays in the server log; the caller gets a generic message.
    logger.exception("Unexpected error in %s", type(operation).__name__)
    return fail(ErrorCode.INTERNAL_ERROR, _UNEXPECTED_MESSAGE)
