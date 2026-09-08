"""Structural check: the deep-dive is present and names the work split."""

from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "architecture.md"

REQUIRED_PHRASES = (
    "queryable map",
    "itemized menu",
    "cheapest-item",
    "dietary",
    "Work packages",
)


def test_architecture_doc_covers_the_product_and_issue_split() -> None:
    text = DOC.read_text(encoding="utf-8")
    lowered = text.lower()
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase.lower() not in lowered]
    assert missing == [], f"architecture.md missing phrases: {missing}"
    assert "WP-1" in text
    assert "WP-3" in text  # map
    assert "WP-4" in text  # menus
    assert "WP-5" in text  # cheapest-item
    assert "WP-6" in text  # dietary
