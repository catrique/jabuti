"""Verify that generated sources satisfy what their workflows expect."""

import json
from pathlib import Path

from prumo.deployment.model import DeploymentTarget, WorkflowTechnology
from prumo.project.config import MigrationStrategy

_REQUIRED_FILES = {
    WorkflowTechnology.PYTHON: ("requirements.txt",),
    WorkflowTechnology.NODE: ("package.json", "package-lock.json"),
    WorkflowTechnology.REACT: ("package.json", "package-lock.json"),
    WorkflowTechnology.ANGULAR: ("package.json", "package-lock.json", "angular.json"),
    WorkflowTechnology.NEXT: ("package.json",),
    WorkflowTechnology.STATIC: ("index.html",),
}
_ANGULAR_APPLICATION_BUILDER = "@angular/build:application"


class DeploymentCheckError(RuntimeError):
    """Raised when a workflow would be generated for an incompatible source."""


def verify_deployment_source(project_root: Path, target: DeploymentTarget) -> None:
    """Ensure SRC, required files, Angular OUT and migrations really exist."""
    source = project_root / target.source
    problems = [
        f"Arquivo ausente: {Path(target.source, name).as_posix()}"
        for name in _REQUIRED_FILES[target.technology]
        if not (source / name).is_file()
    ]

    if not problems and target.technology is WorkflowTechnology.ANGULAR:
        problems.extend(_angular_output_problems(source, target))

    problems.extend(_migration_problems(source, target.migrations))

    if problems:
        raise DeploymentCheckError(
            f"O workflow de {target.app_name} não foi gerado:\n- "
            + "\n- ".join(problems)
        )


def _angular_output_problems(source: Path, target: DeploymentTarget) -> list[str]:
    """Compare the planned OUT with the build configured in angular.json."""
    workspace = json.loads((source / "angular.json").read_text(encoding="utf-8"))
    for name, project in workspace.get("projects", {}).items():
        build = project.get("architect", {}).get("build", {})
        if build.get("builder") != _ANGULAR_APPLICATION_BUILDER:
            continue

        output_path = build.get("options", {}).get("outputPath", f"dist/{name}")
        if isinstance(output_path, dict):
            output_path = output_path.get("base", f"dist/{name}")

        if f"{output_path}/browser" == target.angular_output:
            return []

    return [f"OUT não corresponde ao build do angular.json: {target.angular_output}"]


def _migration_problems(source: Path, strategy: MigrationStrategy) -> list[str]:
    if strategy is MigrationStrategy.ALEMBIC:
        required = ("alembic.ini", "migrations/env.py")
        return [
            f"Arquivo de migrations ausente: {name}"
            for name in required
            if not (source / name).is_file()
        ]

    package_file = source / "package.json"
    if strategy is MigrationStrategy.NPM_SCRIPT and package_file.is_file():
        package = json.loads(package_file.read_text(encoding="utf-8"))
        if "migrar" not in package.get("scripts", {}):
            return ["package.json não possui o script 'migrar'."]

    return []
