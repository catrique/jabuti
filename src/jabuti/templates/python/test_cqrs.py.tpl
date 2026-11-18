import asyncio

from app.application.cqrs import (
    ApplicationError,
    Command,
    CommandHandler,
    CommandResult,
    ErrorCode,
    Query,
    QueryHandler,
    QueryResult,
)


class _Rename(Command[str]):
    def __init__(self, name: str) -> None:
        self.name = name

    def validate(self) -> bool:
        return bool(self.name)

    async def execute(self) -> CommandResult[str]:
        return CommandResult.ok(self.name, rows=1)


class _Missing(Query[str]):
    def execute(self) -> QueryResult[str]:
        raise ApplicationError(ErrorCode.NOT_FOUND, "Not found.")


def test_async_command_runs_after_validation() -> None:
    handler = CommandHandler()

    assert asyncio.run(handler.handle_async(_Rename("new"))).data == "new"
    rejected = asyncio.run(handler.handle_async(_Rename("")))
    assert rejected.error_code is ErrorCode.INVALID_REQUEST


def test_known_query_failure_keeps_its_error_code() -> None:
    result = QueryHandler().handle(_Missing())

    assert not result.success
    assert result.error_code is ErrorCode.NOT_FOUND
