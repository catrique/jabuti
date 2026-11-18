"""Interactive project creation command."""

from collections.abc import Callable
from pathlib import Path

import typer

from jabuti.commands.prompts import PromptCancelled, prompt_project_config
from jabuti.commands.summary import summary_lines
from jabuti.generators.angular import generate_angular
from jabuti.generators.express import generate_express
from jabuti.generators.fastapi import generate_fastapi
from jabuti.generators.flask import generate_flask
from jabuti.generators.process import GenerationError
from jabuti.generators.react import generate_react
from jabuti.prerequisites import PrerequisiteError, Toolchain, check_prerequisites
from jabuti.project.config import Backend, Framework, Frontend
from jabuti.project.planner import (
    ComponentPlan,
    ProjectPlan,
    ProjectTargetExistsError,
    component_directory,
    create_project_structure,
    plan_project,
)
from jabuti.project.repository import write_repository_files

Generator = Callable[[ComponentPlan, Path, Toolchain], None]

_GENERATORS: dict[Framework, Generator] = {
    Frontend.REACT: generate_react,
    Frontend.ANGULAR: generate_angular,
    Backend.FASTAPI: generate_fastapi,
    Backend.FLASK: generate_flask,
    Backend.EXPRESS: generate_express,
}


def create() -> None:
    """Configure e crie um projeto com o Jabuti."""
    try:
        config = prompt_project_config()
    except PromptCancelled:
        typer.echo("Operação cancelada.")
        return

    plan = plan_project(config)
    typer.echo()
    typer.echo("\n".join(summary_lines(plan)))
    typer.echo()

    if not typer.confirm("Continuar?", default=True):
        typer.echo("Operação cancelada.")
        return

    tools = _check_prerequisites(plan)
    project_root = _create_root(plan)
    _generate(plan, project_root, tools)
    _show_success(plan)


def _check_prerequisites(plan: ProjectPlan) -> Toolchain:
    try:
        tools = check_prerequisites(plan)
    except PrerequisiteError as error:
        typer.echo(str(error), err=True)
        typer.echo("\nNenhum arquivo foi criado.", err=True)
        raise typer.Exit(code=1) from None

    for tool in tools.describe():
        typer.echo(f"[OK] {tool}")
    return tools


def _create_root(plan: ProjectPlan) -> Path:
    try:
        return create_project_structure(plan)
    except ProjectTargetExistsError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from None


def _generate(plan: ProjectPlan, project_root: Path, tools: Toolchain) -> None:
    """Generate every component, then the repository files that depend on them."""
    try:
        for component in plan.components:
            generator = _GENERATORS[component.framework]
            generator(component, component_directory(component, project_root), tools)
            typer.echo(f"[OK] {component.framework} criado")

        write_repository_files(plan, project_root)
    except GenerationError as error:
        typer.echo(str(error), err=True)
        typer.echo(
            f"\nA criação foi interrompida. Os arquivos gerados até aqui foram "
            f"mantidos em '{plan.root}' para inspeção.",
            err=True,
        )
        raise typer.Exit(code=1) from None

    typer.echo("[OK] README.md, AGENTS.md e .gitignore gerados")


def _show_success(plan: ProjectPlan) -> None:
    typer.echo("\nProjeto criado com sucesso.")
    for component in plan.components:
        directory = Path(plan.root, component.directory).as_posix()
        typer.echo(f"\nPara iniciar {component.framework}:")
        typer.echo(f"cd {directory}")
        typer.echo(component.stack.run_command)
