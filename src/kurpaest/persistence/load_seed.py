"""Load WP-8 seed JSON through the WP-2 Store."""

from __future__ import annotations

from kurpaest.persistence.store import Store, apply_migrations, connect
from kurpaest.seed import Seed, load_seed


def import_seed(store: Store, seed: Seed | None = None) -> Seed:
    """Save places, menus, and items. Idempotent via Store upserts."""
    records = seed or load_seed()
    for place in records.places:
        store.save_place(place)
    for menu in records.menus:
        store.save_menu(menu)
    for item in records.items:
        store.save_menu_item(item)
    return records


def main() -> None:
    records = load_seed()
    with connect() as conn:
        apply_migrations(conn)
        store = Store(conn)
        import_seed(store, records)
        store.commit()
    print(
        f"imported {len(records.places)} places, "
        f"{len(records.menus)} menus, {len(records.items)} items"
    )


if __name__ == "__main__":
    main()
