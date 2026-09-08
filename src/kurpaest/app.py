"""HTTP seam for kurpaest.lt.

Route handlers validate HTTP and call domain query functions. Cheapest-item,
dietary, and geo logic must not live here.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from kurpaest.catalog import MOCK_PLACES
from kurpaest.domain import Place
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


@app.get("/places")
def list_places(
    bbox: str | None = Query(default=None, description="s,w,n,e WGS84 viewport"),
    city: str | None = Query(default=None),
) -> dict[str, list[dict[str, object]]]:
    """Map pins for the current viewport. Does not download the whole country."""
    try:
        south, west, north, east = parse_bbox(bbox or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    found = places_in_bounds(MOCK_PLACES, south, west, north, east, city=city)
    return {"places": [_place_pin(place) for place in found]}
