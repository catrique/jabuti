"""Detection of a system Python able to create project virtual environments."""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

PythonVersion = tuple[int, int, int]

_MINIMUM_VERSION: PythonVersion = (3, 10, 0)
_VERSION_PATTERN = re.compile(r"^Python (\d+)\.(\d+)\.(\d+)")
# On Windows "python3" is often a Microsoft Store stub, so it is tried last.
_CANDIDATES = ("python", "py", "python3") if os.name == "nt" else ("python3", "python")


class PythonPrerequisiteError(RuntimeError):
    """Raised when no usable Python interpreter is available."""


@dataclass(frozen=True, slots=True)
class PythonInterpreter:
    """System interpreter used only to create project virtual environments."""

    executable: Path
    version: PythonVersion


def detect_python() -> PythonInterpreter:
    """Find a Python interpreter that meets the minimum supported version."""
    for name in _CANDIDATES:
        executable = shutil.which(name)
        if executable is None:
            continue

        version = _read_version(executable)
        if version is not None and version >= _MINIMUM_VERSION:
            return PythonInterpreter(Path(executable), version)

    minimum = ".".join(str(part) for part in _MINIMUM_VERSION[:2])
    raise PythonPrerequisiteError(
        f"Python {minimum}+ é necessário, mas não foi encontrado.\n"
        "Instale uma versão compatível do Python e execute novamente."
    )


def format_python_version(version: PythonVersion) -> str:
    """Format a Python version for user-facing output."""
    return ".".join(str(part) for part in version)


def _read_version(executable: str) -> PythonVersion | None:
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    match = _VERSION_PATTERN.match(result.stdout.strip() or result.stderr.strip())
    if result.returncode != 0 or match is None:
        return None

    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)
