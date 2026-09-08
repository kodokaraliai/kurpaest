"""HTTP seam for kurpaest.lt.

Route handlers validate HTTP and call domain query functions. Cheapest-item,
dietary, and geo logic must not live here.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from kurpaest.catalog import ITEMS, MENUS, PLACES
from kurpaest.dietary import places_with_dietary
from kurpaest.domain import DietaryTag, Menu, MenuItem, Place
from kurpaest.items import MenuItemWithPlace, cheapest_items, parse_near
from kurpaest.menus import menu_for_place, menu_record_for_place, place_by_id
from kurpaest.places import parse_bbox, places_in_bounds

SERVICE_NAME = "kurpaest"
SERVICE_STATUS_OK = "ok"
SITE = "kurpaest.lt"

app = FastAPI(title="kurpaest.lt", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Primary skeleton response: service identity and health."""
    return {
        "service": SERVICE_NAME,
        "status": SERVICE_STATUS_OK,
        "site": SITE,
    }


def _parse_place_id(raw: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="id must be a UUID") from exc


def _hours_payload(place: Place) -> list[dict[str, int]]:
    return [
        {
            "weekday": interval.weekday,
            "open_minute": interval.open_minute,
            "close_minute": interval.close_minute,
        }
        for interval in place.hours
    ]


def _place_pin(place: Place) -> dict[str, object]:
    return {
        "id": str(place.id),
        "name": place.name,
        "slug": place.slug,
        "lat": place.lat,
        "lng": place.lng,
        "address": place.address,
        "city": place.city,
    }


def _place_detail(place: Place, menu: Menu | None) -> dict[str, object]:
    body: dict[str, object] = {
        **_place_pin(place),
        "hours": _hours_payload(place),
        "phone": place.phone,
        "website": place.website,
        "last_verified_at": (
            menu.last_verified_at.isoformat() if menu is not None else None
        ),
        "currency": str(menu.currency) if menu is not None else None,
    }
    return body


def _item_payload(item: MenuItem) -> dict[str, object]:
    return {
        "id": str(item.id),
        "name": item.name,
        "name_en": item.name_en,
        "description": item.description,
        "price_cents": item.price_cents,
        "category": str(item.category),
        "dietary_tags": sorted(str(tag) for tag in item.dietary_tags),
    }


def _item_with_place_payload(row: MenuItemWithPlace) -> dict[str, object]:
    body: dict[str, object] = {
        **_item_payload(row.item),
        "place": _place_pin(row.place),
    }
    if row.distance_m is not None:
        body["distance_m"] = row.distance_m
    return body


def _parse_dietary_query(raw: str | None) -> tuple[DietaryTag, ...]:
    if raw is None or not raw.strip():
        return ()
    tags: list[DietaryTag] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            tags.append(DietaryTag(token))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"unknown dietary tag: {token}",
            ) from exc
    return tuple(tags)


@app.get("/places")
def list_places(
    bbox: str | None = Query(default=None, description="s,w,n,e WGS84 viewport"),
    city: str | None = Query(default=None),
    dietary: str | None = Query(default=None),
) -> dict[str, list[dict[str, object]]]:
    """Map pins for the current viewport. Does not download the whole country."""
    try:
        south, west, north, east = parse_bbox(bbox or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    found = places_in_bounds(PLACES, south, west, north, east, city=city)
    tags = _parse_dietary_query(dietary)
    if tags:
        found = places_with_dietary(found, ITEMS, tags)
    return {"places": [_place_pin(place) for place in found]}


@app.get("/places/{place_id}")
def get_place(place_id: str) -> dict[str, object]:
    """Place detail: pin, hours, menu freshness. 404 if the id is unknown."""
    parsed = _parse_place_id(place_id)
    place = place_by_id(PLACES, parsed)
    if place is None:
        raise HTTPException(status_code=404, detail="place not found")
    menu = menu_record_for_place(MENUS, parsed)
    return _place_detail(place, menu)


@app.get("/places/{place_id}/menu")
def get_place_menu(place_id: str) -> dict[str, object]:
    """Itemized menu for a place. Prices are integer cents; currency EUR."""
    parsed = _parse_place_id(place_id)
    place = place_by_id(PLACES, parsed)
    if place is None:
        raise HTTPException(status_code=404, detail="place not found")
    menu = menu_record_for_place(MENUS, parsed)
    items = menu_for_place(ITEMS, parsed)
    return {
        "place_id": str(place.id),
        "currency": str(menu.currency) if menu is not None else "EUR",
        "last_verified_at": (
            menu.last_verified_at.isoformat() if menu is not None else None
        ),
        "language": str(menu.language) if menu is not None else None,
        "items": [_item_payload(item) for item in items],
    }


@app.get("/items")
def list_items(
    q: str | None = Query(default=None),
    sort: str = Query(default="price"),
    city: str | None = Query(default=None),
    near: str | None = Query(default=None),
    radius_m: int | None = Query(default=None),
    dietary: str | None = Query(default=None),
    limit: int = Query(default=20),
) -> dict[str, list[dict[str, object]]]:
    """Cheapest matching items, each with its place. Literal match; aliases are WP-7."""
    if sort != "price":
        raise HTTPException(status_code=400, detail="sort must be price")
    point = None
    if near is not None or radius_m is not None:
        if near is None or radius_m is None:
            raise HTTPException(
                status_code=400,
                detail="near and radius_m must be provided together",
            )
        try:
            point = parse_near(near)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    tags = _parse_dietary_query(dietary)
    try:
        found = cheapest_items(
            ITEMS,
            PLACES,
            q or "",
            city=city,
            near=point,
            radius_m=float(radius_m) if radius_m is not None else None,
            dietary=tags,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": [_item_with_place_payload(row) for row in found]}
