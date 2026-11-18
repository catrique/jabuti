"""Repository-level files written after every component was generated."""

from pathlib import Path

from jabuti.documentation.agents import render_agents
from jabuti.documentation.readme import render_readme
from jabuti.project.gitignore import write_gitignore
from jabuti.project.planner import ProjectPlan
from jabuti.rendering import write_text_file


def write_repository_files(plan: ProjectPlan, project_root: Path) -> None:
    """Write .gitignore, README and AGENTS."""
    write_text_file(project_root / "README.md", render_readme(plan))
    write_text_file(project_root / "AGENTS.md", render_agents(plan))
    write_gitignore(project_root, plan)

