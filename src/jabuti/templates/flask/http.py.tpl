"""Flask adapter: turn application results into HTTP errors.

Routes decide the successful response themselves: ``render_template`` or
``redirect`` for pages, ``jsonify`` for JSON endpoints.
"""

from typing import TypeVar

from flask import abort

from app.application.cqrs import CommandResult, ErrorCode, QueryResult

T = TypeVar("T")

HTTP_STATUS = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.BAD_GATEWAY: 502,
    ErrorCode.INTERNAL_ERROR: 500,
}


def unwrap(result: CommandResult[T] | QueryResult[T]) -> T | None:
    """Return the result data, or abort with the status for its error code."""
    if result.success:
        return result.data
    code = result.error_code or ErrorCode.INTERNAL_ERROR
    abort(HTTP_STATUS[code], description=result.error_message)
