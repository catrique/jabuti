import pytest

from jabuti.project.config import (
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectConfig,
    ProjectConfigError,
    ProjectType,
    Topology,
    validate_project_name,
)


@pytest.mark.parametrize(
    ("config", "topology"),
    [
        (
            ProjectConfig("portal", ProjectType.FRONTEND, frontend=Frontend.ANGULAR),
            Topology.STANDALONE,
        ),
        (
            ProjectConfig(
                "api",
                ProjectType.API,
                backend=Backend.FASTAPI,
                database=Database.MYSQL,
                migrations=MigrationStrategy.ALEMBIC,
            ),
            Topology.STANDALONE,
        ),
        (
            ProjectConfig(
                "sentinel",
                ProjectType.FULLSTACK,
                frontend=Frontend.REACT,
                backend=Backend.EXPRESS,
            ),
            Topology.SEPARATED,
        ),
        (
            ProjectConfig("painel", ProjectType.WEB_APP, backend=Backend.FLASK),
            Topology.BACKEND_SERVES_FRONTEND,
        ),
    ],
)
def test_topology_follows_project_type(
    config: ProjectConfig,
    topology: Topology,
) -> None:
    assert config.topology is topology


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "project_type": ProjectType.FRONTEND,
            "frontend": Frontend.REACT,
            "database": Database.MYSQL,
        },
        {"project_type": ProjectType.API, "frontend": Frontend.REACT},
        {"project_type": ProjectType.API, "backend": Backend.FLASK},
        {"project_type": ProjectType.WEB_APP, "backend": Backend.FASTAPI},
        {
            "project_type": ProjectType.API,
            "backend": Backend.FASTAPI,
            "migrations": MigrationStrategy.ALEMBIC,
        },
        {
            "project_type": ProjectType.API,
            "backend": Backend.EXPRESS,
            "database": Database.MYSQL,
            "migrations": MigrationStrategy.ALEMBIC,
        },
    ],
)
def test_rejects_choices_incompatible_with_project_type(
    arguments: dict[str, object],
) -> None:
    with pytest.raises(ProjectConfigError):
        ProjectConfig(name="projeto", **arguments)  # type: ignore[arg-type]


def test_angular_rejects_names_the_angular_cli_does_not_accept() -> None:
    with pytest.raises(ProjectConfigError, match="Angular"):
        ProjectConfig("portal_2", ProjectType.FRONTEND, frontend=Frontend.ANGULAR)


@pytest.mark.parametrize("name", ["sentinel", "meu-projeto", "api_2026"])
def test_accepts_safe_project_names(name: str) -> None:
    validate_project_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../teste",
        "../../teste",
        "/tmp/teste",
        "C:\\teste",
        "teste/outro",
        "teste\\outro",
        "a" * 101,
    ],
)
def test_rejects_unsafe_project_names(name: str) -> None:
    with pytest.raises(ProjectConfigError):
        validate_project_name(name)


@pytest.mark.parametrize("name", ["CON", "nul", "COM1", "LPT9"])
def test_rejects_windows_reserved_names(name: str) -> None:
    with pytest.raises(ProjectConfigError):
        validate_project_name(name)
