"""Read-only diagnosis of the local tools used by Prumo."""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from prumo.node import (
    NodePrerequisiteError,
    format_node_version,
    locate_node,
    parse_node_version,
    read_node_version,
)
from prumo.prerequisites import PrerequisiteError, verify_framework_tools
from prumo.project.config import Backend, Framework, Frontend
from prumo.python_runtime import (
    PythonPrerequisiteError,
    detect_python,
    format_python_version,
    python_version_requirement,
)

DIAGNOSED_STACKS: tuple[Framework, ...] = (
    Frontend.REACT,
    Frontend.ANGULAR,
    Backend.FASTAPI,
    Backend.FLASK,
    Backend.EXPRESS,
)
_VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


@dataclass(frozen=True, slots=True)
class ToolCheck:
    """A system tool and the version found, if any."""

    name: str
    version: str | None
    problem: str = ""

    @property
    def ok(self) -> bool:
        return self.version is not None


@dataclass(frozen=True, slots=True)
class StackCheck:
    """Whether the environment can create one stack, and why not."""

    framework: Framework
    problem: str | None

    @property
    def ok(self) -> bool:
        return self.problem is None


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """Result of inspecting the environment."""

    tools: tuple[ToolCheck, ...]
    stacks: tuple[StackCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.ok for check in (*self.tools, *self.stacks))


def diagnose() -> Diagnosis:
    """Inspect tools and stacks. Never installs or changes anything."""
    return Diagnosis(
        tools=(_check_python(), *_check_node(), _check_git()),
        stacks=tuple(_check_stack(framework) for framework in DIAGNOSED_STACKS),
    )


def _check_stack(framework: Framework) -> StackCheck:
    """Apply exactly the same rules used by prumo create."""
    try:
        verify_framework_tools(framework)
    except PrerequisiteError as error:
        return StackCheck(framework, str(error))
    return StackCheck(framework, None)


def _check_python() -> ToolCheck:
    try:
        interpreter = detect_python()
    except PythonPrerequisiteError:
        return ToolCheck(
            "Python",
            None,
            f"não encontrado ({python_version_requirement()} necessário)",
        )
    return ToolCheck("Python", format_python_version(interpreter.version))


def _check_node() -> tuple[ToolCheck, ToolCheck]:
    installation = locate_node()

    node_version = None
    if installation.node_executable is not None:
        try:
            raw_version = read_node_version(installation.node_executable)
        except NodePrerequisiteError:
            raw_version = ""
        parsed = parse_node_version(raw_version)
        node_version = format_node_version(parsed) if parsed else None

    npm_version = (
        _tool_version(installation.npm_executable)
        if installation.npm_executable is not None
        else None
    )
    return (
        ToolCheck("Node.js", node_version, "" if node_version else "não encontrado"),
        ToolCheck("npm", npm_version, "" if npm_version else "não encontrado"),
    )


def _check_git() -> ToolCheck:
    executable = shutil.which("git")
    version = _tool_version(Path(executable)) if executable else None
    return ToolCheck("Git", version, "" if version else "não encontrado")


def _tool_version(executable: Path) -> str | None:
    """Version number printed by `<tool> --version`, or None."""
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    match = _VERSION_PATTERN.search(result.stdout)
    return match.group(1) if result.returncode == 0 and match else None
