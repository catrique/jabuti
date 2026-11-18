"""Run the real generators with external commands stubbed out."""

import asyncio
import importlib
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from jabuti.commands.create import _generate
from jabuti.node import NodeToolchain
from jabuti.prerequisites import Toolchain
from jabuti.project.config import (
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectConfig,
    ProjectType,
)
from jabuti.project.planner import create_project_structure, plan_project
from jabuti.python_runtime import PythonInterpreter

TOOLS = Toolchain(
    node=NodeToolchain(Path("node"), Path("npm"), (22, 22, 3)),
    python=PythonInterpreter(Path("python"), (3, 12, 0)),
)
CQRS_PYTHON = "app/application/cqrs/handlers.py"
CQRS_EXPRESS = "src/application/cqrs/handlers.js"


def _stub_external_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(arguments: list[str], **_options: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(arguments, 0, stdout="fastapi==1.0\n")

    monkeypatch.setattr("jabuti.generators.process.subprocess.run", run)
    monkeypatch.setattr("jabuti.generators.react.subprocess.run", run)


@pytest.fixture
def generate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[ProjectConfig], Path]:
    _stub_external_commands(monkeypatch)

    def create(config: ProjectConfig) -> Path:
        plan = plan_project(config)
        root = create_project_structure(plan, tmp_path)
        _generate(plan, root, TOOLS)
        return root

    return create


def generated_files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def api(backend: Backend, **options: Any) -> ProjectConfig:
    return ProjectConfig("portal", ProjectType.API, backend=backend, **options)


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.REACT),
            {
                "src/application/cqrs.ts",
                "src/infrastructure/api/client.ts",
                "src/infrastructure/api/config.ts",
            },
        ),
        (
            ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.ANGULAR),
            {
                "src/app/application/cqrs.ts",
                "src/app/infrastructure/api/api-client.ts",
                "src/environments/environment.ts",
                "src/environments/environment.development.ts",
            },
        ),
        (api(Backend.FASTAPI), {CQRS_PYTHON, "app/http.py", "tests/test_cqrs.py"}),
        (
            ProjectConfig(
                "portal",
                ProjectType.WEB_APP,
                backend=Backend.FLASK,
                database=Database.MYSQL,
                migrations=MigrationStrategy.ALEMBIC,
            ),
            {
                CQRS_PYTHON,
                "app/http.py",
                "app/config.py",
                "app/infrastructure/database.py",
                "alembic.ini",
                "migrations/env.py",
                ".env.example",
            },
        ),
        (
            api(Backend.EXPRESS, database=Database.MYSQL),
            {
                CQRS_EXPRESS,
                "src/http.js",
                "src/infrastructure/database.js",
                "tests/cqrs.test.js",
            },
        ),
    ],
)
def test_scaffold_has_cqrs_layers_and_no_leftovers(
    config: ProjectConfig,
    expected: set[str],
    generate: Callable[[ProjectConfig], Path],
) -> None:
    files = generated_files(generate(config))

    assert expected <= set(files)
    assert {"AGENTS.md", "README.md", ".gitignore"} <= set(files)
    assert not any(name.startswith(".github/") for name in files)
    assert not any("/modules/" in f"/{name}" for name in files)
    assert ".env" not in files
    leftovers = [name for name, text in files.items() if "%%" in text]
    assert leftovers == []
    assert "Lightweight CQRS" in files["AGENTS.md"]


def test_fullstack_frontend_and_backend_know_each_other(
    generate: Callable[[ProjectConfig], Path],
) -> None:
    root = generate(
        ProjectConfig(
            "portal",
            ProjectType.FULLSTACK,
            frontend=Frontend.REACT,
            backend=Backend.EXPRESS,
        )
    )

    frontend_env = (root / "frontend" / ".env.example").read_text(encoding="utf-8")
    backend_env = (root / "backend" / ".env.example").read_text(encoding="utf-8")
    assert "VITE_API_BASE_URL=http://localhost:3000" in frontend_env
    assert "FRONTEND_ORIGINS=http://localhost:5173" in backend_env
    assert not (root / "frontend" / "src" / "application" / "cqrs").exists()
    assert (root / "backend" / CQRS_EXPRESS).is_file()


@pytest.fixture
def cqrs(
    generate: Callable[[ProjectConfig], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[ModuleType]:
    """The generated, framework-independent Python CQRS package."""
    root = generate(api(Backend.FASTAPI))
    monkeypatch.syspath_prepend(str(root))
    yield importlib.import_module("app.application.cqrs")
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]


def test_python_cqrs_does_not_import_web_framework_or_database(
    generate: Callable[[ProjectConfig], Path],
) -> None:
    root = generate(api(Backend.FASTAPI, database=Database.MYSQL))

    for module in (root / "app" / "application" / "cqrs").glob("*.py"):
        source = module.read_text(encoding="utf-8")
        for dependency in ("fastapi", "flask", "sqlalchemy", "http"):
            assert f"import {dependency}" not in source.lower(), module.name
            assert f"from {dependency}" not in source.lower(), module.name


def test_python_cqrs_runs_sync_and_async_operations(cqrs: ModuleType) -> None:
    class SyncCommand(cqrs.Command):
        def execute(self) -> Any:
            return cqrs.CommandResult.ok("sync", rows=1)

    class AsyncCommand(cqrs.Command):
        async def execute(self) -> Any:
            return cqrs.CommandResult.ok("async")

    class SyncQuery(cqrs.Query):
        def execute(self) -> Any:
            return cqrs.QueryResult.ok({"id": 1})

    class AsyncListing(cqrs.Query):
        async def execute(self) -> Any:
            return cqrs.QueryResult.ok([1, 2], total_rows=500)

    commands, queries = cqrs.CommandHandler(), cqrs.QueryHandler()

    assert commands.handle(SyncCommand()).rows == 1
    assert asyncio.run(commands.handle_async(AsyncCommand())).data == "async"
    single = queries.handle(SyncQuery())
    assert (single.success, single.total_rows) == (True, None)
    assert asyncio.run(queries.handle_async(AsyncListing())).total_rows == 500
    with pytest.raises(TypeError):
        commands.handle(AsyncCommand())


def test_python_cqrs_reports_rejections_and_errors(cqrs: ModuleType) -> None:
    code = cqrs.ErrorCode

    class Invalid(cqrs.Command):
        def validate(self) -> bool:
            return False

        def execute(self) -> Any:
            raise AssertionError("must not run")

    class Forbidden(cqrs.Query):
        def has_permission(self) -> bool:
            return False

        def execute(self) -> Any:
            raise AssertionError("must not run")

    class Conflict(cqrs.Command):
        async def execute(self) -> Any:
            raise cqrs.ApplicationError(code.CONFLICT, "Already exists.")

    class Broken(cqrs.Query):
        def execute(self) -> Any:
            raise RuntimeError("secret detail")

    commands, queries = cqrs.CommandHandler(), cqrs.QueryHandler()

    assert commands.handle(Invalid()).error_code is code.INVALID_REQUEST
    assert queries.handle(Forbidden()).error_code is code.FORBIDDEN
    conflict = asyncio.run(commands.handle_async(Conflict()))
    assert (conflict.error_code, conflict.error_message) == (
        code.CONFLICT,
        "Already exists.",
    )
    broken = queries.handle(Broken())
    assert broken.error_code is code.INTERNAL_ERROR
    assert "secret" not in (broken.error_message or "")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not available")
def test_express_cqrs_runs_on_node(generate: Callable[[ProjectConfig], Path]) -> None:
    root = generate(api(Backend.EXPRESS))

    result = subprocess.run(
        ["node", "--test", "tests/cqrs.test.js"],
        cwd=root,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
