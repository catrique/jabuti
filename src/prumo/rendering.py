"""Render the text templates shipped inside the Prumo package."""

import re
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

_PLACEHOLDER = re.compile(r"%%([A-Z_]+)%%")


class TemplateRenderError(RuntimeError):
    """Raised when a template references a value that was not provided."""


def render_template(name: str, values: Mapping[str, str] | None = None) -> str:
    """Replace every %%KEY%% placeholder of a packaged template."""
    provided = values or {}
    template = files("prumo").joinpath("templates", *name.split("/"))
    text = template.read_text(encoding="utf-8")

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in provided:
            raise TemplateRenderError(f"Valor ausente para {key} em {name}.")
        return provided[key]

    return _PLACEHOLDER.sub(substitute, text)


def write_text_file(target: Path, content: str) -> None:
    """Write a generated text file with LF line endings."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def write_template(
    target: Path,
    name: str,
    values: Mapping[str, str] | None = None,
) -> None:
    """Render a packaged template into a project file."""
    write_text_file(target, render_template(name, values))
