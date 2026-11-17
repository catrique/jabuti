"""Command-line interface for Jabuti."""

import typer

from jabuti import __version__
from jabuti.commands.create import create
from jabuti.commands.doctor import doctor

app = typer.Typer(
    name="jabuti",
    help="Jabuti: uma base para criar e padronizar projetos de software.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Crie e padronize projetos de software com o Jabuti."""


@app.command()
def version() -> None:
    """Exibe a versão atual do Jabuti."""
    typer.echo(f"Jabuti {__version__}")


app.command()(create)
app.command()(doctor)
