"""Environment variable examples written into generated projects."""

from collections.abc import Sequence
from pathlib import Path

from jabuti.rendering import write_text_file

# Placeholders only: real credentials are always provided by the developer.
DATABASE_VARIABLES = (
    "DB_HOST=localhost",
    "DB_PORT=3306",
    "DB_NAME=",
    "DB_USER=",
    "DB_PASSWORD=",
)


def write_env_example(target_directory: Path, variables: Sequence[str]) -> None:
    """Write a versionable .env.example; the real .env is never generated."""
    write_text_file(target_directory / ".env.example", "\n".join(variables) + "\n")
