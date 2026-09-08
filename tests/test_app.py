"""Drive the shipped HTTP entry — the real FastAPI app, not a stand-in."""

from fastapi.testclient import TestClient

from kurpaest.app import SERVICE_NAME, SERVICE_STATUS_OK, SITE, app, root
from kurpaest.catalog import PLACES

VILNIUS_BBOX = "54.66,25.22,54.71,25.34"
LITHUANIA_BBOX = "53.8,20.9,56.5,26.9"


def test_root_handler_returns_service_identity() -> None:
    body = root()
    assert body["service"] == SERVICE_NAME
    assert body["status"] == SERVICE_STATUS_OK
    assert body["site"] == SITE


def test_root_http_serves_the_same_body_as_the_handler() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == root()


def test_places_requires_bbox() -> None:
    response = TestClient(app).get("/places")
    assert response.status_code == 400
    assert "bbox" in response.json()["detail"]


def test_places_rejects_malformed_bbox() -> None:
    response = TestClient(app).get("/places", params={"bbox": "not-a-box"})
    assert response.status_code == 400


def test_places_vilnius_viewport_returns_pins_not_the_whole_country() -> None:
    client = TestClient(app)
    vilnius = client.get("/places", params={"bbox": VILNIUS_BBOX})
    wide = client.get("/places", params={"bbox": LITHUANIA_BBOX})
    assert vilnius.status_code == 200
    assert wide.status_code == 200
    vilnius_places = vilnius.json()["places"]
    wide_places = wide.json()["places"]
    assert vilnius_places
    assert all(pin["city"] == "Vilnius" for pin in vilnius_places)
    vilnius_slugs = {pin["slug"] for pin in vilnius_places}
    wide_slugs = {pin["slug"] for pin in wide_places}
    assert "senamiescio-kebabine" in vilnius_slugs
    assert "fabijoniskiu-valgykla" not in vilnius_slugs
    assert "fabijoniskiu-valgykla" in wide_slugs
    assert vilnius_slugs < wide_slugs
    for pin in vilnius_places:
        assert isinstance(pin["lat"], float)
        assert isinstance(pin["lng"], float)
        assert pin["name"]
        assert pin["id"]


def test_places_city_filter() -> None:
    client = TestClient(app)
    vilnius = client.get(
        "/places",
        params={"bbox": LITHUANIA_BBOX, "city": "Vilnius"},
    )
    kaunas = client.get(
        "/places",
        params={"bbox": LITHUANIA_BBOX, "city": "Kaunas"},
    )
    assert vilnius.status_code == 200
    assert kaunas.status_code == 200
    assert {pin["slug"] for pin in vilnius.json()["places"]} == {
        place.slug for place in PLACES
    }
    assert kaunas.json() == {"places": []}


def test_places_empty_viewport() -> None:
    response = TestClient(app).get(
        "/places",
        params={"bbox": "0,0,1,1"},
    )
    assert response.status_code == 200
    assert response.json() == {"places": []}


def test_seed_catalog_is_what_the_http_seam_serves() -> None:
    slugs = {place.slug for place in PLACES}
    assert "senamiescio-kebabine" in slugs
    assert "saknys" in slugs
    assert "fabijoniskiu-valgykla" in slugs
