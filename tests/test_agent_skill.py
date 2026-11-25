"""Guard the repository's independent CLI and Agent Skill entry points."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "jabuti" / "SKILL.md"


def test_official_skill_has_discoverable_metadata() -> None:
    content = SKILL.read_text(encoding="utf-8")
    opening, frontmatter, body = content.split("---\n", maxsplit=2)
    metadata = dict(line.split(": ", maxsplit=1) for line in frontmatter.splitlines())

    assert opening == ""
    assert metadata["name"] == SKILL.parent.name == "jabuti"
    assert 0 < len(metadata["description"]) <= 1024
    assert body.strip()


def test_readme_documents_official_installation_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "pip install jabuti" in readme
    for agents in ("-a claude-code", "-a codex", "-a claude-code -a codex"):
        assert f"npx skills add catrique/jabuti --skill jabuti {agents} -g -y" in readme


def test_public_usage_documents_do_not_restore_legacy_infrastructure() -> None:
    for document in (SKILL, ROOT / "README.md"):
        content = document.read_text(encoding="utf-8").lower()
        for legacy in (
            "/opt/",
            "pm2",
            "rsync",
            "deploy_root",
            "deploy_user",
            "prumo",
            "private key",
        ):
            assert legacy not in content, (document.name, legacy)
