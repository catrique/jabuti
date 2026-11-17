"""Detection and validation of the Node.js toolchain."""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

NodeVersion = tuple[int, int, int]

_NODE_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


class NodePrerequisiteError(RuntimeError):
    """Raised when the Node.js toolchain cannot be used."""


@dataclass(frozen=True, slots=True)
class NodeRequirement:
    """Node.js version lines accepted by a tool used by a generator."""

    tool: str
    baselines: tuple[NodeVersion, ...]


VITE_REQUIREMENT = NodeRequirement("Vite", ((20, 19, 0), (22, 12, 0)))
EXPRESS_REQUIREMENT = NodeRequirement("Express", ((20, 19, 0), (22, 12, 0)))
ANGULAR_REQUIREMENT = NodeRequirement("Angular CLI", ((22, 22, 3), (24, 15, 0)))


@dataclass(frozen=True, slots=True)
class NodeToolchain:
    """Executables and version required to generate Node.js projects."""

    node_executable: Path
    npm_executable: Path
    node_version: NodeVersion


def detect_node_toolchain(
    requirement: NodeRequirement = VITE_REQUIREMENT,
) -> NodeToolchain:
    """Locate Node.js and npm and ensure the Node.js version is supported."""
    node_executable = shutil.which("node")
    if node_executable is None:
        raise NodePrerequisiteError(
            f"{requirement.tool} requer Node.js, mas ele não foi encontrado.\n"
            "Instale uma versão compatível do Node.js e execute novamente."
        )

    npm_executable = _find_npm()
    if npm_executable is None:
        raise NodePrerequisiteError(
            f"{requirement.tool} requer npm, mas ele não foi encontrado."
        )

    version_output = _read_node_version(node_executable)
    node_version = parse_node_version(version_output)
    if node_version is None:
        raise NodePrerequisiteError(
            "Não foi possível interpretar a versão instalada do Node.js.\n"
            f"Encontrado: {version_output or 'saída vazia'}\n"
            f"Necessário: {node_version_requirement(requirement)}"
        )

    if not is_node_version_compatible(node_version, requirement):
        raise NodePrerequisiteError(
            "A versão instalada do Node.js não é compatível com "
            f"{requirement.tool}.\n"
            f"Encontrado: {format_node_version(node_version)}\n"
            f"Necessário: {node_version_requirement(requirement)}"
        )

    return NodeToolchain(
        node_executable=Path(node_executable),
        npm_executable=Path(npm_executable),
        node_version=node_version,
    )


def parse_node_version(value: str) -> NodeVersion | None:
    """Parse the version format returned by node --version."""
    match = _NODE_VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        return None

    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def is_node_version_compatible(
    version: NodeVersion,
    requirement: NodeRequirement = VITE_REQUIREMENT,
) -> bool:
    """Return whether a Node.js version meets a supported baseline."""
    for baseline in requirement.baselines:
        if version[0] == baseline[0]:
            return version >= baseline

    return version[0] > requirement.baselines[-1][0]


def format_node_version(version: NodeVersion) -> str:
    """Format a Node.js version for user-facing output."""
    return ".".join(str(part) for part in version)


def node_version_requirement(
    requirement: NodeRequirement = VITE_REQUIREMENT,
) -> str:
    """Describe the supported Node.js version lines."""
    baselines = [
        f"{format_node_version(baseline)}+" for baseline in requirement.baselines
    ]
    return f"Node {' ou '.join(baselines)}"


def _find_npm() -> str | None:
    candidates = ("npm.cmd", "npm.exe", "npm") if os.name == "nt" else ("npm",)
    return next(
        (executable for name in candidates if (executable := shutil.which(name))),
        None,
    )


def _read_node_version(node_executable: str) -> str:
    try:
        result = subprocess.run(
            [node_executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError):
        raise NodePrerequisiteError(
            "Não foi possível consultar a versão instalada do Node.js."
        ) from None

    return result.stdout.strip()
