"""Safe execution of the external commands used by generators."""

import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


class GenerationError(RuntimeError):
    """Raised when a generator cannot complete one of its steps."""


def run_step(
    arguments: Sequence[str | Path],
    cwd: Path,
    failure_message: str,
    extra_environment: Mapping[str, str] | None = None,
) -> None:
    """Run a command as an argument list, without a shell."""
    environment = {**os.environ, **extra_environment} if extra_environment else None
    try:
        subprocess.run(
            [str(argument) for argument in arguments],
            cwd=cwd,
            check=True,
            shell=False,
            env=environment,
        )
    except (OSError, subprocess.CalledProcessError):
        raise GenerationError(failure_message) from None


def capture_step(
    arguments: Sequence[str | Path],
    cwd: Path,
    failure_message: str,
) -> str:
    """Run a command without a shell and return its standard output."""
    try:
        result = subprocess.run(
            [str(argument) for argument in arguments],
            cwd=cwd,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        raise GenerationError(failure_message) from None

    return result.stdout
