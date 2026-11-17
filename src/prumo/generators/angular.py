"""Angular project generation with the official CLI, run through npm exec."""

from pathlib import Path

from prumo.generators.process import run_step
from prumo.prerequisites import Toolchain
from prumo.project.planner import ComponentPlan

# Pinned major version so the build output layout stays predictable.
_ANGULAR_CLI_PACKAGE = "@angular/cli@22"


def generate_angular(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Create an Angular workspace directly inside the target directory."""
    run_step(
        [
            tools.npm,
            "exec",
            "--yes",
            f"--package={_ANGULAR_CLI_PACKAGE}",
            "--",
            "ng",
            "new",
            component.project_name,
            "--directory",
            ".",
            "--defaults",
            "--interactive=false",
            "--skip-git",
            "--package-manager",
            "npm",
            "--style",
            "css",
            "--ssr=false",
            "--ai-config",
            "none",
        ],
        cwd=target_directory,
        failure_message="Não foi possível criar o projeto Angular.",
        extra_environment={"NG_CLI_ANALYTICS": "false"},
    )
