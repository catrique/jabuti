"""Repository-level files written after every component was generated."""

from pathlib import Path

from jabuti.deployment.checks import verify_deployment_source
from jabuti.deployment.workflows import render_workflows
from jabuti.documentation.agents import render_agents
from jabuti.documentation.readme import render_readme
from jabuti.project.gitignore import write_gitignore
from jabuti.project.planner import WORKFLOWS_DIRECTORY, ProjectPlan
from jabuti.rendering import write_text_file


def write_repository_files(plan: ProjectPlan, project_root: Path) -> None:
    """Write workflows (when enabled), .gitignore, README and AGENTS."""
    files: dict[Path, str] = {}
    if plan.config.deploy_workflows:
        files.update(_workflow_files(plan, project_root))
    files[Path("README.md")] = render_readme(plan)
    files[Path("AGENTS.md")] = render_agents(plan)

    for relative_path, content in files.items():
        write_text_file(project_root / relative_path, content)
    write_gitignore(project_root, plan)


def _workflow_files(plan: ProjectPlan, project_root: Path) -> dict[Path, str]:
    """Verify every source first, so no workflow is written for a broken one."""
    targets = [component.deployment for component in plan.components]
    for target in targets:
        verify_deployment_source(project_root, target)

    return {
        WORKFLOWS_DIRECTORY / name: content
        for target in targets
        for name, content in render_workflows(target).items()
    }
