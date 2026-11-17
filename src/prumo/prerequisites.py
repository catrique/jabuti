"""Check the system tools required by the components of a plan."""

from dataclasses import dataclass
from pathlib import Path

from prumo.node import (
    ANGULAR_REQUIREMENT,
    EXPRESS_REQUIREMENT,
    VITE_REQUIREMENT,
    NodePrerequisiteError,
    NodeRequirement,
    NodeToolchain,
    detect_node_toolchain,
    format_node_version,
)
from prumo.project.config import Backend, Framework, Frontend
from prumo.project.planner import ProjectPlan
from prumo.project.stacks import Runtime, stack_for
from prumo.python_runtime import (
    PythonInterpreter,
    PythonPrerequisiteError,
    detect_python,
    format_python_version,
)

PrerequisiteError = (NodePrerequisiteError, PythonPrerequisiteError)

_NODE_REQUIREMENTS: dict[Framework, NodeRequirement] = {
    Frontend.REACT: VITE_REQUIREMENT,
    Frontend.ANGULAR: ANGULAR_REQUIREMENT,
    Backend.EXPRESS: EXPRESS_REQUIREMENT,
}


@dataclass(frozen=True, slots=True)
class Toolchain:
    """System tools found for the current plan."""

    node: NodeToolchain | None = None
    python: PythonInterpreter | None = None

    @property
    def npm(self) -> Path:
        """npm executable; only available when the plan needs Node.js."""
        assert self.node is not None, "Node.js não foi verificado para este plano."
        return self.node.npm_executable

    @property
    def python_executable(self) -> Path:
        """System Python; only available when the plan needs Python."""
        assert self.python is not None, "Python não foi verificado para este plano."
        return self.python.executable

    def describe(self) -> list[str]:
        """Human-readable list of the tools that were found."""
        found = []
        if self.node is not None:
            version = format_node_version(self.node.node_version)
            found.extend((f"Node.js encontrado ({version})", "npm encontrado"))
        if self.python is not None:
            version = format_python_version(self.python.version)
            found.append(f"Python encontrado ({version})")
        return found


def verify_framework_tools(
    framework: Framework,
) -> NodeToolchain | PythonInterpreter:
    """Verify, without installing anything, the tools one framework needs."""
    if stack_for(framework).runtime is Runtime.PYTHON:
        return detect_python()
    return detect_node_toolchain(_NODE_REQUIREMENTS[framework])


def check_prerequisites(plan: ProjectPlan) -> Toolchain:
    """Verify the tools needed by every component of a plan."""
    node = None
    python = None
    for component in plan.components:
        tools = verify_framework_tools(component.framework)
        if isinstance(tools, NodeToolchain):
            node = tools
        else:
            python = tools
    return Toolchain(node=node, python=python)
