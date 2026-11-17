"""Root .gitignore combining the patterns needed by every component."""

from pathlib import Path

from jabuti.project.planner import ProjectPlan
from jabuti.project.stacks import Runtime
from jabuti.rendering import write_text_file

_RUNTIME_PATTERNS = {
    Runtime.PYTHON: (".venv/", "venv/", "__pycache__/", "*.pyc"),
    Runtime.NODE: ("node_modules/", "dist/"),
}
# .env.example stays versioned; every real .env file is ignored.
_ENVIRONMENT_PATTERNS = (".env", ".env.*", "!.env.example")
_SECTION_HEADER = "# Jabuti"


def gitignore_patterns(plan: ProjectPlan) -> list[str]:
    """Patterns required by the runtimes used in the plan, without repeats."""
    runtimes = dict.fromkeys(component.stack.runtime for component in plan.components)
    patterns = [
        pattern for runtime in runtimes for pattern in _RUNTIME_PATTERNS[runtime]
    ]
    return [*patterns, *_ENVIRONMENT_PATTERNS]


def write_gitignore(project_root: Path, plan: ProjectPlan) -> None:
    """Append missing patterns, keeping any .gitignore a scaffold created."""
    gitignore = project_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    present = {_normalize(line) for line in existing.splitlines()}
    missing = [
        pattern
        for pattern in gitignore_patterns(plan)
        if _normalize(pattern) not in present
    ]
    if not missing:
        return

    prefix = existing.rstrip("\n") + "\n\n" if existing.strip() else ""
    write_text_file(
        gitignore,
        prefix + "\n".join([_SECTION_HEADER, *missing]) + "\n",
    )


def _normalize(pattern: str) -> str:
    return pattern.strip().strip("/")
