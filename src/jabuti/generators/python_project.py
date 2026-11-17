"""Virtual environment, dependencies and database support for Python backends."""

import os
from collections.abc import Sequence
from pathlib import Path

from jabuti.generators.environment import DATABASE_VARIABLES, write_env_example
from jabuti.generators.process import capture_step, run_step
from jabuti.prerequisites import Toolchain
from jabuti.project.config import Database, MigrationStrategy
from jabuti.project.planner import ComponentPlan
from jabuti.rendering import write_template, write_text_file

_DATABASE_PACKAGES = ("SQLAlchemy", "PyMySQL[rsa]", "python-dotenv")
_ALEMBIC_PACKAGES = ("alembic",)


def prepare_python_project(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
    packages: Sequence[str],
) -> None:
    """Add database support, create .venv, install packages and pin them."""
    all_packages = [*packages]
    if component.database is Database.MYSQL:
        _write_database_support(target_directory)
        all_packages.extend(_DATABASE_PACKAGES)
    if component.migrations is MigrationStrategy.ALEMBIC:
        _write_alembic(target_directory)
        all_packages.extend(_ALEMBIC_PACKAGES)

    venv_python = _create_virtualenv(target_directory, tools.python_executable)
    run_step(
        [venv_python, "-m", "pip", "install", "--disable-pip-version-check",
         *all_packages],
        cwd=target_directory,
        failure_message="Não foi possível instalar as dependências Python na .venv.",
    )
    _freeze_requirements(venv_python, target_directory)


def _write_database_support(target_directory: Path) -> None:
    write_template(target_directory / "app" / "config.py", "python/config.py.tpl")
    write_template(
        target_directory / "app" / "database.py",
        "python/database.py.tpl",
    )
    write_env_example(target_directory, DATABASE_VARIABLES)


def _write_alembic(target_directory: Path) -> None:
    migrations = target_directory / "migrations"
    write_template(target_directory / "alembic.ini", "python/alembic.ini.tpl")
    write_template(migrations / "env.py", "python/migrations/env.py.tpl")
    write_template(
        migrations / "script.py.mako",
        "python/migrations/script.py.mako.tpl",
    )
    write_text_file(migrations / "versions" / ".gitkeep", "")


def _create_virtualenv(target_directory: Path, system_python: Path) -> Path:
    run_step(
        [system_python, "-m", "venv", ".venv"],
        cwd=target_directory,
        failure_message="Não foi possível criar a .venv do projeto.",
    )
    if os.name == "nt":
        return target_directory / ".venv" / "Scripts" / "python.exe"
    return target_directory / ".venv" / "bin" / "python"


def _freeze_requirements(venv_python: Path, target_directory: Path) -> None:
    """Pin the project environment, leaving out references to local paths."""
    frozen = capture_step(
        [venv_python, "-m", "pip", "freeze", "--exclude-editable"],
        cwd=target_directory,
        failure_message="Não foi possível gerar o requirements.txt.",
    )
    requirements = [
        line
        for line in frozen.splitlines()
        if line.strip() and " @ file:" not in line
    ]
    write_text_file(
        target_directory / "requirements.txt",
        "\n".join(requirements) + "\n",
    )
