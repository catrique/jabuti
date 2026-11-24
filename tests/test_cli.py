from enum import StrEnum
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jabuti import __version__
from jabuti.cli import app
from jabuti.commands import create as create_command
from jabuti.generators.process import GenerationError
from jabuti.node import NodePrerequisiteError
from jabuti.prerequisites import Toolchain
from jabuti.project.config import (
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectType,
)
from jabuti.project.planner import ComponentPlan, ProjectPlan

runner = CliRunner()


def configure_menu_selections(
    monkeypatch: pytest.MonkeyPatch,
    selections: tuple[StrEnum, ...],
) -> list[tuple[str, tuple[StrEnum, ...]]]:
    selected = iter(selections)
    prompts: list[tuple[str, tuple[StrEnum, ...]]] = []

    def choose(
        message: str,
        options: tuple[tuple[str, StrEnum], ...],
    ) -> StrEnum:
        values = tuple(value for _title, value in options)
        value = next(selected)
        assert value in values
        prompts.append((message, values))
        return value

    monkeypatch.setattr("jabuti.commands.prompts.select_option", choose)
    return prompts


def fake_generator(component: ComponentPlan, target: Path, _tools: Toolchain) -> None:
    """Stand-in generator that creates only the local migration files."""
    if component.migrations is MigrationStrategy.ALEMBIC:
        (target / "alembic.ini").write_text("", encoding="utf-8")
        (target / "migrations").mkdir()
        (target / "migrations" / "env.py").write_text("", encoding="utf-8")


@pytest.fixture
def fake_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "jabuti.commands.create.check_prerequisites",
        lambda _plan: Toolchain(),
    )
    for framework in (*Frontend, *Backend):
        monkeypatch.setitem(create_command._GENERATORS, framework, fake_generator)
    return tmp_path


def test_help_displays_jabuti_presentation() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "create" in result.output
    assert "version" in result.output


def test_version_displays_current_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output == f"Jabuti {__version__}\n"


FULLSTACK_ALEMBIC = (
    ProjectType.FULLSTACK,
    Frontend.REACT,
    Backend.FASTAPI,
    Database.MYSQL,
    MigrationStrategy.ALEMBIC,
)


@pytest.mark.parametrize(
    "selections",
    [
        (ProjectType.FRONTEND, Frontend.REACT),
        (ProjectType.FRONTEND, Frontend.ANGULAR),
        (ProjectType.API, Backend.EXPRESS, Database.NONE),
        FULLSTACK_ALEMBIC,
        (ProjectType.WEB_APP, Backend.FLASK, Database.MYSQL, MigrationStrategy.ALEMBIC),
    ],
)
def test_created_project_has_agents_readme_and_no_workflows(
    selections: tuple[StrEnum, ...],
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, selections)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    project = fake_environment / "portal"
    assert result.exit_code == 0, result.output
    assert ".env" in (project / ".gitignore").read_text(encoding="utf-8")
    assert not (project / ".github").exists()
    for document in ("README.md", "AGENTS.md"):
        content = (project / document).read_text(encoding="utf-8").lower()
        assert "lightweight cqrs" in content
        assert "deploy" not in content
        assert "workflow" not in content


def test_fullstack_keeps_local_alembic_migrations(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, FULLSTACK_ALEMBIC)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    project = fake_environment / "portal"
    assert result.exit_code == 0, result.output
    assert (project / "frontend").is_dir()
    assert (project / "backend" / "alembic.ini").is_file()
    for document in ("README.md", "AGENTS.md"):
        content = (project / document).read_text(encoding="utf-8")
        assert "alembic upgrade head" in content


@pytest.mark.parametrize(
    ("selections", "command"),
    [
        (
            (ProjectType.API, Backend.FASTAPI, Database.NONE),
            "python -m uvicorn app.main:app --reload",
        ),
        (
            (ProjectType.WEB_APP, Backend.FLASK, Database.NONE),
            "python -m flask --app app run --debug",
        ),
    ],
)
def test_python_success_instructions_use_activated_environment(
    selections: tuple[StrEnum, ...],
    command: str,
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, selections)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    assert result.exit_code == 0, result.output
    assert "Ative .venv conforme o README.md" in result.output
    assert command in result.output
    assert ".venv/bin/python" not in result.output
    assert r".venv\Scripts\python.exe" not in result.output


def test_frontend_does_not_ask_backend_or_database(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts = configure_menu_selections(
        monkeypatch,
        (ProjectType.FRONTEND, Frontend.REACT),
    )

    result = runner.invoke(app, ["create"], input="portal\nn\n")

    assert result.exit_code == 0
    assert [message for message, _options in prompts] == [
        "O que você quer criar?",
        "Framework:",
    ]
    assert "Operação cancelada." in result.output
    assert not (fake_environment / "portal").exists()


def test_missing_tool_stops_before_creating_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_menu_selections(monkeypatch, (ProjectType.FRONTEND, Frontend.REACT))

    def fail_prerequisite_check(_plan: ProjectPlan) -> Toolchain:
        raise NodePrerequisiteError("Node.js não encontrado.")

    monkeypatch.setattr(
        "jabuti.commands.create.check_prerequisites",
        fail_prerequisite_check,
    )

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    assert result.exit_code == 1
    assert "Nenhum arquivo foi criado." in result.output
    assert not (tmp_path / "portal").exists()


def test_generation_failure_is_reported_without_traceback(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, (ProjectType.FRONTEND, Frontend.REACT))

    def fail(_component: ComponentPlan, _target: Path, _tools: Toolchain) -> None:
        raise GenerationError("Falha esperada do Vite.")

    monkeypatch.setitem(create_command._GENERATORS, Frontend.REACT, fail)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    assert result.exit_code == 1
    assert "Falha esperada do Vite." in result.output
    assert "Traceback" not in result.output
