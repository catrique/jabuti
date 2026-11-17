import pytest
from typer.testing import CliRunner

from jabuti import doctor, node, python_runtime
from jabuti.cli import app
from jabuti.doctor import diagnose
from jabuti.project.config import Backend, Frontend


def fake_environment(
    monkeypatch: pytest.MonkeyPatch,
    available: set[str],
    node_version: str = "v22.23.1",
) -> None:
    """Simulate executables on PATH; no real tool is executed."""

    def which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in available else None

    for module in (node, doctor, python_runtime):
        monkeypatch.setattr(module.shutil, "which", which)
    monkeypatch.setattr(node, "read_node_version", lambda _path: node_version)
    monkeypatch.setattr(doctor, "read_node_version", lambda _path: node_version)
    monkeypatch.setattr(python_runtime, "_read_version", lambda _path: (3, 12, 0))
    monkeypatch.setattr(doctor, "_tool_version", lambda _path: "1.0.0")


EVERYTHING = {"node", "npm", "git", "python", "python3"}


def test_complete_environment_is_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_environment(monkeypatch, EVERYTHING)

    diagnosis = diagnose()

    assert diagnosis.ready
    assert [tool.version for tool in diagnosis.tools] == [
        "3.12.0",
        "22.23.1",
        "1.0.0",
        "1.0.0",
    ]


def test_angular_uses_its_own_node_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_environment(monkeypatch, EVERYTHING, node_version="v22.20.0")

    stacks = {check.framework: check.ok for check in diagnose().stacks}

    assert stacks == {
        Frontend.REACT: True,
        Frontend.ANGULAR: False,
        Backend.FASTAPI: True,
        Backend.FLASK: True,
        Backend.EXPRESS: True,
    }


def test_missing_tools_are_reported_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_environment(monkeypatch, {"git"})

    diagnosis = diagnose()
    result = CliRunner().invoke(app, ["doctor"])

    assert not any(check.ok for check in diagnosis.stacks)
    assert [tool.ok for tool in diagnosis.tools] == [False, False, False, True]
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)
