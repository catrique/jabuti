"""Turn planned deployment targets into GitHub Actions workflow files."""

import re
import textwrap

from jabuti.deployment.model import (
    DeploymentScope,
    DeploymentTarget,
    WorkflowTechnology,
)
from jabuti.project.config import (
    MigrationStrategy,
    ProjectConfigError,
    validate_project_name,
)
from jabuti.rendering import render_template

_SOURCE_PATTERN = re.compile(r"^(\.|[a-z]+)$")
_OUTPUT_SEGMENT = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
_MIGRATION_TEMPLATES = {
    MigrationStrategy.ALEMBIC: "workflows/migrations-python.yml.tpl",
    MigrationStrategy.NPM_SCRIPT: "workflows/migrations-node.yml.tpl",
}
# Indentation of a shell line inside a step's `run: |` block.
_RUN_INDENT = " " * 10


class WorkflowConfigurationError(ValueError):
    """Raised when a deployment target cannot be safely rendered."""


def render_workflows(target: DeploymentTarget) -> dict[str, str]:
    """Render the workflows of a target, keyed by file name."""
    validate_target(target)
    workflows = {target.deploy_workflow: _render_deploy(target)}

    if target.migrations_workflow is not None:
        workflows[target.migrations_workflow] = _render_migrations(target)

    return workflows


def validate_target(target: DeploymentTarget) -> None:
    """Reject values that are unsafe to embed in a workflow script."""
    try:
        validate_project_name(target.app_name)
    except ProjectConfigError as error:
        raise WorkflowConfigurationError(f"APP inválido: {error}") from None

    if not _SOURCE_PATTERN.fullmatch(target.source):
        raise WorkflowConfigurationError(f"SRC inválido: {target.source}")

    if not isinstance(target.technology, WorkflowTechnology):
        raise WorkflowConfigurationError(f"TIPO inválido: {target.technology}")

    is_angular = target.technology is WorkflowTechnology.ANGULAR
    if is_angular != (target.angular_output is not None):
        raise WorkflowConfigurationError("OUT deve existir somente para Angular.")

    if target.angular_output is not None and not _is_safe_relative_path(
        target.angular_output
    ):
        raise WorkflowConfigurationError(f"OUT inválido: {target.angular_output}")


def _render_deploy(target: DeploymentTarget) -> str:
    output = (
        f"  OUT: '{target.angular_output}'\n" if target.angular_output else ""
    )
    return render_template(
        "workflows/deploy.yml.tpl",
        {
            "WORKFLOW_NAME": target.workflow_title("Deploy"),
            "PUSH_FILTER": _push_filter(target),
            "APP": target.app_name,
            "SRC": target.source,
            "TIPO": target.technology.value,
            "OUT_ENV": output,
            "LOCKFILE": _source_file(target, "package-lock.json"),
            "RESOLVE_TARGET": _resolve_target_script(),
        },
    )


def _render_migrations(target: DeploymentTarget) -> str:
    return render_template(
        _MIGRATION_TEMPLATES[target.migrations],
        {
            "WORKFLOW_NAME": target.workflow_title("Migrations"),
            "APP": target.app_name,
            "RESOLVE_TARGET": _resolve_target_script(),
        },
    )


def _resolve_target_script() -> str:
    """Shared shell that validates DEPLOY_ROOT and APP before any change."""
    script = render_template("workflows/resolve-target.sh.tpl")
    return textwrap.indent(script, _RUN_INDENT).rstrip("\n")


def _source_file(target: DeploymentTarget, name: str) -> str:
    """Path of a file inside SRC, relative to the repository root."""
    if target.source == ".":
        return name
    return f"{target.source}/{name}"


def _push_filter(target: DeploymentTarget) -> str:
    """Paths that trigger a deploy; migrations alone never trigger one."""
    if target.scope is None:
        return "    paths-ignore:\n      - 'migrations/**'"

    patterns = [f"{target.source}/**"]
    if target.scope is DeploymentScope.BACKEND:
        patterns.append(f"!{target.source}/migrations/**")
    patterns.append(f".github/workflows/{target.deploy_workflow}")

    lines = "\n".join(f"      - '{pattern}'" for pattern in patterns)
    return f"    paths:\n{lines}"


def _is_safe_relative_path(value: str) -> bool:
    segments = value.split("/")
    return all(
        _OUTPUT_SEGMENT.fullmatch(segment) and segment not in {".", ".."}
        for segment in segments
    )
