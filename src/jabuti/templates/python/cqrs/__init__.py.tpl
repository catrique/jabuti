"""Lightweight CQRS primitives, independent of web framework and database."""

from app.application.cqrs.command import Command
from app.application.cqrs.errors import ApplicationError, ErrorCode
from app.application.cqrs.handlers import CommandHandler, QueryHandler
from app.application.cqrs.query import Query
from app.application.cqrs.results import CommandResult, QueryResult

__all__ = [
    "ApplicationError",
    "Command",
    "CommandHandler",
    "CommandResult",
    "ErrorCode",
    "Query",
    "QueryHandler",
    "QueryResult",
]
