"""Angular project generation with the official CLI, run through npm exec."""

from pathlib import Path

from jabuti.generators.process import run_step
from jabuti.prerequisites import Toolchain
from jabuti.project.planner import ComponentPlan
from jabuti.rendering import write_template

# Pinned major version so the build output layout stays predictable.
_ANGULAR_CLI_PACKAGE = "@angular/cli@22"
_NO_ANALYTICS = {"NG_CLI_ANALYTICS": "false"}
# CQRS primitives and the single HTTP entry point of the application.
_ARCHITECTURE_FILES = {
    "src/app/application/cqrs.ts": "angular/cqrs.ts.tpl",
    "src/app/infrastructure/api/api-client.ts": "angular/api-client.ts.tpl",
}


def generate_angular(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Create the Angular workspace, its environments and the CQRS/API layers."""
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
        extra_environment=_NO_ANALYTICS,
    )
    # Official environment files, wired by the CLI into angular.json.
    run_step(
        [tools.npm, "exec", "--", "ng", "generate", "environments"],
        cwd=target_directory,
        failure_message="Não foi possível criar os environments do Angular.",
        extra_environment=_NO_ANALYTICS,
    )
    environments = {
        "environment.ts": "",
        "environment.development.ts": component.api_base_url or "",
    }
    for name, api_base_url in environments.items():
        write_template(
            target_directory / "src" / "environments" / name,
            "angular/environment.ts.tpl",
            {"API_BASE_URL": api_base_url},
        )
    for relative_path, template in _ARCHITECTURE_FILES.items():
        write_template(target_directory / relative_path, template)
