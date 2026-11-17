"""Deployment targets and the naming rules for published applications."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from jabuti.project.config import MigrationStrategy

DEPLOY_ROOT = PurePosixPath("/srv/apps")

_SEPARATED_BACKEND_SUFFIX = "-api"


class WorkflowTechnology(StrEnum):
    """Values accepted by the TIPO variable of the deploy workflow."""

    PYTHON = "python"
    NODE = "node"
    REACT = "react"
    ANGULAR = "angular"
    NEXT = "next"
    STATIC = "static"


class DeploymentScope(StrEnum):
    """Role of a target when a repository publishes more than one application."""

    FRONTEND = "frontend"
    BACKEND = "backend"


def separated_backend_app_name(repository: str) -> str:
    """Server name of the backend when frontend and backend are separated."""
    return f"{repository}{_SEPARATED_BACKEND_SUFFIX}"


@dataclass(frozen=True, slots=True)
class DeploymentTarget:
    """One application published by its own deploy workflow."""

    app_name: str
    source: str
    technology: WorkflowTechnology
    scope: DeploymentScope | None = None
    angular_output: str | None = None
    migrations: MigrationStrategy = MigrationStrategy.NONE

    @property
    def server_path(self) -> PurePosixPath:
        """Directory where the application is published on the server."""
        return DEPLOY_ROOT / self.app_name

    @property
    def deploy_workflow(self) -> str:
        """File name of the deploy workflow."""
        return self._workflow_file("deploy")

    @property
    def migrations_workflow(self) -> str | None:
        """File name of the migrations workflow, when migrations exist."""
        if self.migrations is MigrationStrategy.NONE:
            return None
        return self._workflow_file("migrations")

    def workflow_title(self, base: str) -> str:
        """Human title of a workflow, qualified by scope when needed."""
        return f"{base} {self.scope.value.title()}" if self.scope else base

    def _workflow_file(self, base: str) -> str:
        return f"{base}-{self.scope}.yml" if self.scope else f"{base}.yml"
