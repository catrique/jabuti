from pathlib import Path

import pytest

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


def test_fullstack_separates_frontend_and_backend_directories() -> None:
    plan = plan_project(SENTINEL)
    frontend, backend = plan.components

    assert plan.directories == ("frontend", "backend")
    assert (frontend.framework, backend.framework) == (Frontend.REACT, Backend.FASTAPI)
    assert frontend.database is Database.NONE
    assert frontend.migrations is MigrationStrategy.NONE
    assert backend.migrations is MigrationStrategy.ALEMBIC


def test_standalone_component_lives_at_repository_root() -> None:
    config = ProjectConfig("portal-rh", ProjectType.API, backend=Backend.EXPRESS)
    plan = plan_project(config)

    (component,) = plan.components

    assert component.directory == "."
    assert plan.directories == ()


def test_existing_destination_is_not_modified(tmp_path: Path) -> None:
    target = tmp_path / "portal"
    target.mkdir()
    existing_file = target / "important.txt"
    existing_file.write_text("preserve", encoding="utf-8")

    with pytest.raises(ProjectTargetExistsError):
        create_project_structure(plan_project(REACT), tmp_path)

    assert existing_file.read_text(encoding="utf-8") == "preserve"
    assert list(target.iterdir()) == [existing_file]
