"""Operator launcher starts the API and Vite UI together."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run.sh"


def test_run_script_is_executable() -> None:
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111


def test_run_script_starts_api_and_vite() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "#!/usr/bin/env bash" in text
    assert "uv sync --group dev" in text
    assert "uv run kurpaest" in text
    assert "npm install" in text
    assert "npm run dev" in text
    assert "127.0.0.1:8000" in text
    assert "127.0.0.1:5173" in text
    assert "file://" in text
    assert "need uv" in text
    assert "need node" in text
    assert "need npm" in text


def test_readme_points_at_run_script() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "./scripts/run.sh" in text
    assert "http://127.0.0.1:5173/" in text
    assert "file://" in text
