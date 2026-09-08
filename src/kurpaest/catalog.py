"""In-memory place catalog for the map until WP-8 seed data lands."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid5

from kurpaest.domain import Place, PlaceSource

_NAMESPACE = UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
_VERIFIED_AT = datetime(2026, 9, 8, tzinfo=UTC)


def _place_id(slug: str) -> UUID:
    return uuid5(_NAMESPACE, f"https://kurpaest.lt/places/{slug}")


# Vilnius pins sit inside a typical zoom-13 viewport around the old town.
# Kaunas is outside that viewport so bbox filtering is observable.
MOCK_PLACES: tuple[Place, ...] = (
    Place(
        id=_place_id("senamiescio-kebabine"),
        name="Senamiesčio kebabinė",
        slug="senamiescio-kebabine",
        lat=54.6818,
        lng=25.2874,
        address="Pilies g. 8, Vilnius",
        city="Vilnius",
        hours=(),
        source=PlaceSource.SEED,
        updated_at=_VERIFIED_AT,
    ),
    Place(
        id=_place_id("naujamiescio-picerija"),
        name="Naujamiesčio picerija",
        slug="naujamiescio-picerija",
        lat=54.6765,
        lng=25.2752,
        address="Naugarduko g. 12, Vilnius",
        city="Vilnius",
        hours=(),
        source=PlaceSource.SEED,
        updated_at=_VERIFIED_AT,
    ),
    Place(
        id=_place_id("zveryno-valgykla"),
        name="Žvėryno valgykla",
        slug="zveryno-valgykla",
        lat=54.6931,
        lng=25.2684,
        address="Vytauto g. 5, Vilnius",
        city="Vilnius",
        hours=(),
        source=PlaceSource.SEED,
        updated_at=_VERIFIED_AT,
    ),
    Place(
        id=_place_id("kauno-kebabas"),
        name="Kauno kebabas",
        slug="kauno-kebabas",
        lat=54.8969,
        lng=23.8925,
        address="Laisvės al. 40, Kaunas",
        city="Kaunas",
        hours=(),
        source=PlaceSource.SEED,
        updated_at=_VERIFIED_AT,
    ),
)
