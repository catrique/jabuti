"""React project generation with Vite."""

import subprocess
from pathlib import Path

from jabuti.generators.environment import write_env_example
from jabuti.generators.process import GenerationError
from jabuti.prerequisites import Toolchain
from jabuti.project.planner import ComponentPlan
from jabuti.rendering import write_template

_VITE_CREATE_ARGUMENTS = (
    "create",
    "vite@latest",
    ".",
    "--",
    "--template",
    "react-ts",
    "--no-interactive",
)
# CQRS primitives and the single HTTP entry point of the application.
_ARCHITECTURE_FILES = {
    "src/application/cqrs.ts": "react/cqrs.ts.tpl",
    "src/infrastructure/api/config.ts": "react/config.ts.tpl",
    "src/infrastructure/api/client.ts": "react/client.ts.tpl",
}


class ReactScaffoldError(GenerationError):
    """Raised when Vite cannot scaffold the React project."""


class ReactDependencyInstallError(GenerationError):
    """Raised when npm cannot install the React project dependencies."""


def generate_react(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Generate the Vite project, then add the CQRS and API layers."""
    generate_react_project(target_directory, tools.npm)
    for relative_path, template in _ARCHITECTURE_FILES.items():
        write_template(target_directory / relative_path, template)
    write_env_example(
        target_directory,
        [f"VITE_API_BASE_URL={component.api_base_url or ''}"],
    )


def generate_react_project(target_directory: Path, npm_executable: Path) -> None:
    """Create a React TypeScript project and install its dependencies."""
    try:
        subprocess.run(
            [str(npm_executable), *_VITE_CREATE_ARGUMENTS],
            cwd=target_directory,
            check=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ReactScaffoldError(
            "Não foi possível criar o projeto React com o Vite."
        ) from None

    try:
        subprocess.run(
            [str(npm_executable), "install"],
            cwd=target_directory,
            check=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ReactDependencyInstallError(
            "O projeto React foi criado, mas a instalação das dependências falhou."
        ) from None
