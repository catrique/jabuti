import json
from enum import StrEnum
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jabuti import __version__
from jabuti.cli import app
from jabuti.commands import create as create_command
from jabuti.commands.prompts import DeployWorkflows
from jabuti.deployment.model import WorkflowTechnology
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
    """Create only the files that the workflows of a component require."""
    if component.deployment.technology is WorkflowTechnology.PYTHON:
        (target / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    else:
        (target / "package.json").write_text("{}", encoding="utf-8")
        (target / "package-lock.json").write_text("{}", encoding="utf-8")
    if component.framework is Frontend.ANGULAR:
        workspace = {
            "projects": {
                component.project_name: {
                    "architect": {
                        "build": {"builder": "@angular/build:application"}
                    }
                }
            }
        }
        (target / "angular.json").write_text(json.dumps(workspace), encoding="utf-8")
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


YES = DeployWorkflows.YES
FULLSTACK_ALEMBIC = (
    ProjectType.FULLSTACK,
    Frontend.REACT,
    Backend.FASTAPI,
    Database.MYSQL,
    MigrationStrategy.ALEMBIC,
)


@pytest.mark.parametrize(
    ("selections", "workflows"),
    [
        ((ProjectType.FRONTEND, Frontend.REACT, YES), {"deploy.yml"}),
        ((ProjectType.FRONTEND, Frontend.ANGULAR, YES), {"deploy.yml"}),
        ((ProjectType.API, Backend.EXPRESS, Database.NONE, YES), {"deploy.yml"}),
        (
            (*FULLSTACK_ALEMBIC, YES),
            {"deploy-frontend.yml", "deploy-backend.yml", "migrations-backend.yml"},
        ),
        (
            (
                ProjectType.WEB_APP,
                Backend.FLASK,
                Database.MYSQL,
                MigrationStrategy.ALEMBIC,
                YES,
            ),
            {"deploy.yml", "migrations.yml"},
        ),
    ],
)
def test_created_project_has_agents_readme_and_planned_workflows(
    selections: tuple[StrEnum, ...],
    workflows: set[str],
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, selections)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    project = fake_environment / "portal"
    assert result.exit_code == 0, result.output
    assert (project / "AGENTS.md").is_file()
    assert "DEPLOY_ROOT" in (project / "README.md").read_text(encoding="utf-8")
    assert ".env" in (project / ".gitignore").read_text(encoding="utf-8")
    generated = {path.name for path in (project / ".github" / "workflows").iterdir()}
    assert generated == workflows


def test_project_without_deploy_has_no_workflows(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, (*FULLSTACK_ALEMBIC, DeployWorkflows.NO))

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    project = fake_environment / "portal"
    assert result.exit_code == 0, result.output
    assert not (project / ".github").exists()
    assert (project / "backend" / "alembic.ini").is_file()
    for document in ("README.md", "AGENTS.md"):
        content = (project / document).read_text(encoding="utf-8")
        assert "DEPLOY_ROOT" not in content
        assert ".github/workflows" not in content


def test_frontend_does_not_ask_backend_or_database(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts = configure_menu_selections(
        monkeypatch,
        (ProjectType.FRONTEND, Frontend.REACT, YES),
    )

    result = runner.invoke(app, ["create"], input="portal\nn\n")

    assert result.exit_code == 0
    assert [message for message, _options in prompts] == [
        "O que você quer criar?",
        "Framework:",
        "Deseja gerar workflows de deploy?",
    ]
    assert "Operação cancelada." in result.output
    assert not (fake_environment / "portal").exists()


def test_missing_tool_stops_before_creating_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_menu_selections(monkeypatch, (ProjectType.FRONTEND, Frontend.REACT, YES))

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


def test_generation_failure_is_reported_without_traceback_or_workflows(
    fake_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_menu_selections(monkeypatch, (ProjectType.FRONTEND, Frontend.REACT, YES))

    def fail(_component: ComponentPlan, _target: Path, _tools: Toolchain) -> None:
        raise GenerationError("Falha esperada do Vite.")

    monkeypatch.setitem(create_command._GENERATORS, Frontend.REACT, fail)

    result = runner.invoke(app, ["create"], input="portal\ny\n")

    assert result.exit_code == 1
    assert "Falha esperada do Vite." in result.output
    assert "Traceback" not in result.output
    assert not (fake_environment / "portal" / ".github").exists()
