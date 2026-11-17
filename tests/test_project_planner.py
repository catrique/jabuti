import re
from dataclasses import replace
from pathlib import Path

import pytest

from jabuti.deployment.workflows import WorkflowConfigurationError, render_workflows
from jabuti.project.config import (
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectConfig,
    ProjectType,
)
from jabuti.project.planner import (
    ProjectTargetExistsError,
    create_project_structure,
    plan_project,
)

REACT = ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.REACT)
SENTINEL = ProjectConfig(
    "sentinel",
    ProjectType.FULLSTACK,
    frontend=Frontend.REACT,
    backend=Backend.FASTAPI,
    database=Database.MYSQL,
    migrations=MigrationStrategy.ALEMBIC,
)


def rendered_workflows(config: ProjectConfig) -> dict[str, str]:
    workflows: dict[str, str] = {}
    for component in plan_project(config).components:
        workflows.update(render_workflows(component.deployment))
    return workflows


def test_separated_backend_is_published_as_repository_api() -> None:
    frontend, backend = plan_project(SENTINEL).components

    assert (frontend.directory, frontend.deployment.app_name) == (
        "frontend",
        "sentinel",
    )
    assert (backend.directory, backend.deployment.app_name) == (
        "backend",
        "sentinel-api",
    )
    assert backend.deployment.server_path == "<DEPLOY_ROOT>/sentinel-api"
    assert frontend.database is Database.NONE
    assert frontend.migrations is MigrationStrategy.NONE


def test_standalone_api_keeps_repository_name() -> None:
    config = ProjectConfig("portal-rh", ProjectType.API, backend=Backend.EXPRESS)

    (component,) = plan_project(config).components

    assert component.directory == "."
    assert component.deployment.app_name == "portal-rh"


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (REACT, {"deploy.yml"}),
        (
            replace(SENTINEL, migrations=MigrationStrategy.NONE),
            {"deploy-frontend.yml", "deploy-backend.yml"},
        ),
        (
            SENTINEL,
            {"deploy-frontend.yml", "deploy-backend.yml", "migrations-backend.yml"},
        ),
        (
            ProjectConfig(
                "painel",
                ProjectType.WEB_APP,
                backend=Backend.FLASK,
                database=Database.MYSQL,
                migrations=MigrationStrategy.ALEMBIC,
            ),
            {"deploy.yml", "migrations.yml"},
        ),
    ],
)
def test_workflow_files_follow_the_plan(
    config: ProjectConfig,
    expected: set[str],
) -> None:
    workflows = rendered_workflows(config)

    assert set(workflows) == expected
    assert all("%%" not in content for content in workflows.values())


def test_fullstack_workflows_publish_each_side_to_its_own_app() -> None:
    workflows = rendered_workflows(SENTINEL)

    frontend = workflows["deploy-frontend.yml"]
    backend = workflows["deploy-backend.yml"]
    assert "APP: 'sentinel'" in frontend and "SRC: 'frontend'" in frontend
    assert "TIPO: 'react'" in frontend
    assert "APP: 'sentinel-api'" in backend and "SRC: 'backend'" in backend
    assert "TIPO: 'python'" in backend
    assert "'!backend/migrations/**'" in backend
    migrations = workflows["migrations-backend.yml"]
    assert "APP: 'sentinel-api'" in migrations
    assert "DEPLOY_ROOT: ${{ vars.DEPLOY_ROOT }}" in migrations
    assert "working-directory" not in migrations
    assert "push:" not in migrations


@pytest.mark.parametrize(
    "config",
    [
        REACT,
        ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.ANGULAR),
        ProjectConfig("portal-rh", ProjectType.API, backend=Backend.EXPRESS),
        SENTINEL,
    ],
)
def test_workflows_read_server_settings_from_github_variables(
    config: ProjectConfig,
) -> None:
    for name, content in rendered_workflows(config).items():
        assert "${{ vars.DEPLOY_ROOT }}" in content, name
        assert "/opt/" not in content, name
        assert "%%" not in content, name
        # Any other user is only reachable through the DEPLOY_USER variable.
        for command in re.findall(r"sudo .*", content):
            assert '-u "$DEPLOY_USER"' in command, (name, command)


def test_angular_workflow_receives_build_output() -> None:
    config = ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.ANGULAR)

    workflow = rendered_workflows(config)["deploy.yml"]

    assert "OUT: 'dist/portal/browser'" in workflow


@pytest.mark.parametrize(
    "change",
    [{"app_name": "../outro"}, {"source": "../fora"}, {"angular_output": "x"}],
)
def test_unsafe_deployment_values_are_rejected(change: dict[str, str]) -> None:
    target = plan_project(REACT).components[0].deployment

    with pytest.raises(WorkflowConfigurationError):
        render_workflows(replace(target, **change))


def test_existing_destination_is_not_modified(tmp_path: Path) -> None:
    target = tmp_path / "portal"
    target.mkdir()
    existing_file = target / "important.txt"
    existing_file.write_text("preserve", encoding="utf-8")

    with pytest.raises(ProjectTargetExistsError):
        create_project_structure(plan_project(REACT), tmp_path)

    assert existing_file.read_text(encoding="utf-8") == "preserve"
    assert list(target.iterdir()) == [existing_file]
