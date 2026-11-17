"""Environment diagnosis command."""

import typer

from jabuti import __version__
from jabuti.doctor import Diagnosis, diagnose

_SEPARATOR = "-" * 32
_NAME_WIDTH = 10


def doctor() -> None:
    """Verifique as ferramentas do ambiente sem alterar o sistema."""
    diagnosis = diagnose()
    typer.echo("\n".join(report_lines(diagnosis)))
    if not diagnosis.ready:
        raise typer.Exit(code=1)


def report_lines(diagnosis: Diagnosis) -> list[str]:
    """Human-readable report, using only ASCII markers."""
    lines = [f"Jabuti {__version__}", "", "Ambiente", _SEPARATOR]
    for tool in diagnosis.tools:
        detail = tool.version if tool.ok else tool.problem
        lines.append(f"{_marker(tool.ok)} {tool.name:<{_NAME_WIDTH}}{detail}")

    lines.extend(("", "Stacks", _SEPARATOR))
    for stack in diagnosis.stacks:
        lines.append(f"{_marker(stack.ok)} {stack.framework}")
        if stack.problem:
            lines.extend(f"     {line}" for line in stack.problem.splitlines())

    lines.append("")
    if diagnosis.ready:
        lines.append("Ambiente pronto.")
    else:
        lines.append(
            "Algumas ferramentas estão ausentes ou incompatíveis. "
            "O Jabuti não instala nada: instale-as e execute jabuti doctor novamente."
        )
    return lines


def _marker(ok: bool) -> str:
    return "[OK]" if ok else "[--]"
