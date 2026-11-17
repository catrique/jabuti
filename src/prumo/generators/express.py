"""Express generation, as an API or as a server-side web application."""

import json
from pathlib import Path

from prumo.generators.environment import DATABASE_VARIABLES, write_env_example
from prumo.generators.process import run_step
from prumo.prerequisites import Toolchain
from prumo.project.config import Database
from prumo.project.planner import ComponentPlan
from prumo.rendering import write_template, write_text_file

_PORT_VARIABLE = "PORT=3000"


def generate_express(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Create the Express sources, package.json and install dependencies."""
    _write_package_json(component, target_directory)
    for relative_path, template in _source_files(component).items():
        write_template(
            target_directory / relative_path,
            template,
            {"PROJECT_NAME": component.project_name},
        )

    variables = [_PORT_VARIABLE]
    if component.database is Database.MYSQL:
        variables.extend(DATABASE_VARIABLES)
    write_env_example(target_directory, variables)

    run_step(
        [tools.npm, "install", "--no-audit", "--no-fund", *_packages(component)],
        cwd=target_directory,
        failure_message="Não foi possível instalar as dependências do Express.",
    )


def _source_files(component: ComponentPlan) -> dict[str, str]:
    files = {
        "src/server.js": "express/server.js.tpl",
        "tests/health.test.js": "express/health.test.js.tpl",
    }
    if component.serves_frontend:
        files["src/app.js"] = "express/app-web.js.tpl"
        files["views/index.ejs"] = "express/index.ejs.tpl"
        files["public/styles.css"] = "web/styles.css.tpl"
    else:
        files["src/app.js"] = "express/app-api.js.tpl"
    if component.database is Database.MYSQL:
        files["src/database.js"] = "express/database.js.tpl"
    return files


def _packages(component: ComponentPlan) -> list[str]:
    packages = ["express"]
    if component.serves_frontend:
        packages.append("ejs")
    if component.database is Database.MYSQL:
        packages.append("mysql2")
    return packages


def _write_package_json(component: ComponentPlan, target_directory: Path) -> None:
    package = {
        "name": component.deployment.app_name.lower(),
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "main": "src/server.js",
        "scripts": {
            "start": "node src/server.js",
            "dev": "node --watch src/server.js",
            "test": "node --test",
        },
        "engines": {"node": ">=20.19"},
    }
    write_text_file(
        target_directory / "package.json",
        json.dumps(package, indent=2) + "\n",
    )
