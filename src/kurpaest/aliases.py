"""Search alias table and Lithuanian diacritic folding. No HTTP imports.

Matching uses folded forms. Display names stay as stored.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence

from kurpaest.domain import AliasRecord

ALIASES: tuple[AliasRecord, ...] = (
    AliasRecord(
        term="kebab",
        expansions=(
            "kebab",
            "kebabas",
            "doner",
            "döner",
            "shawarma",
            "saurma",
            "šaurma",
            "giros",
        ),
    ),
    AliasRecord(
        term="cepelinai",
        expansions=("cepelinai", "didžkukuliai"),
    ),
)


def fold_diacritics(text: str) -> str:
    """Lowercase and strip combining marks (`š`→`s`, `ė`→`e`, `ö`→`o`)."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return stripped.lower()


def expand_term(
    term: str,
    aliases: Sequence[AliasRecord] = ALIASES,
) -> tuple[str, ...]:
    """Folded query plus alias-group tokens, if the query sits in a group."""
    folded = fold_diacritics(term.strip())
    if not folded:
        return ()
    tokens = {folded}
    for record in aliases:
        group = {fold_diacritics(record.term)}
        group.update(fold_diacritics(token) for token in record.expansions)
        if folded in group:
            tokens.update(group)
    return tuple(sorted(tokens))
