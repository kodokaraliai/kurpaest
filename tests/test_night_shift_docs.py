"""Operator launch docs for night shift stay pointed at this repo."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_night_shift_launch_doc_covers_tmux_restart_and_this_repo() -> None:
    text = (ROOT / "docs/agents/night-shift.md").read_text(encoding="utf-8")
    assert "tmux kill-session -t night-shift" in text
    assert "./scripts/night-shift.sh" in text
    assert "kodokaraliai/kurpaest" in text
    assert "git checkout main" in text
    assert "uv run pytest" in text
    assert "npm run build" in text
    assert "frontend/" in text
    assert "setup_22.x" in text
    assert "nodejs" in text
    assert "ready-for-agent" in text

    script = (ROOT / "scripts/night-shift.sh").read_text(encoding="utf-8")
    assert "docs/agents/night-shift.md" in script
    assert 'REPO="kodokaraliai/kurpaest"' in script
    assert "command -v grok" in script
    assert "command -v gh" in script
    assert "command -v node" in script
    assert "command -v npm" in script


def test_agents_md_points_at_night_shift() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "### Night shift" in text
    assert "docs/agents/night-shift.md" in text


def test_night_shift_script_is_executable() -> None:
    path = ROOT / "scripts" / "night-shift.sh"
    assert path.is_file()
    assert path.stat().st_mode & 0o111
