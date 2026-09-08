"""Drive the shipped HTTP entry — the real FastAPI app, not a stand-in."""

from uuid import uuid4

from fastapi.testclient import TestClient

from kurpaest.app import SERVICE_NAME, SERVICE_STATUS_OK, SITE, app, root
from kurpaest.catalog import ITEMS, MENUS, PLACES
from kurpaest.menus import menu_for_place, menu_record_for_place

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


def _kebab_place():
    return next(place for place in PLACES if place.slug == "senamiescio-kebabine")


def test_place_detail_returns_hours_and_last_verified_at() -> None:
    place = _kebab_place()
    menu = menu_record_for_place(MENUS, place.id)
    assert menu is not None
    response = TestClient(app).get(f"/places/{place.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(place.id)
    assert body["name"] == place.name
    assert body["slug"] == place.slug
    assert body["address"] == place.address
    assert body["city"] == "Vilnius"
    assert isinstance(body["lat"], float)
    assert isinstance(body["lng"], float)
    assert body["hours"]
    assert body["hours"][0]["weekday"] == 0
    assert body["last_verified_at"] == menu.last_verified_at.isoformat()
    assert body["currency"] == "EUR"


def test_place_detail_unknown_id_is_404() -> None:
    response = TestClient(app).get(f"/places/{uuid4()}")
    assert response.status_code == 404


def test_place_detail_rejects_non_uuid() -> None:
    response = TestClient(app).get("/places/senamiescio-kebabine")
    assert response.status_code == 400
    assert "UUID" in response.json()["detail"]


def test_place_menu_lists_priced_items() -> None:
    place = _kebab_place()
    expected = menu_for_place(ITEMS, place.id)
    response = TestClient(app).get(f"/places/{place.id}/menu")
    assert response.status_code == 200
    body = response.json()
    assert body["place_id"] == str(place.id)
    assert body["currency"] == "EUR"
    assert body["last_verified_at"]
    assert len(body["items"]) == len(expected)
    names = [item["name"] for item in body["items"]]
    assert names == [item.name for item in expected]
    for row, item in zip(body["items"], expected, strict=True):
        assert row["price_cents"] == item.price_cents
        assert isinstance(row["price_cents"], int)
        assert row["category"] == str(item.category)
        assert row["dietary_tags"] == sorted(str(tag) for tag in item.dietary_tags)
        assert "search_tokens" not in row
    doner = next(row for row in body["items"] if row["name"] == "Döner")
    assert doner["dietary_tags"] == ["halal"]
    assert doner["name_en"] == "Doner"


def test_place_menu_unknown_id_is_404() -> None:
    response = TestClient(app).get(f"/places/{uuid4()}/menu")
    assert response.status_code == 404


def test_items_alias_giros_and_saurma_hit_kebab_rows() -> None:
    client = TestClient(app)
    giros = client.get("/items", params={"q": "giros", "sort": "price"})
    saurma = client.get("/items", params={"q": "šaurma", "sort": "price"})
    cepelinai = client.get("/items", params={"q": "didžkukuliai"})
    assert giros.status_code == 200
    assert saurma.status_code == 200
    assert cepelinai.status_code == 200
    giros_items = giros.json()["items"]
    assert giros_items[0]["name"] == "Kebabas"
    assert giros_items[0]["price_cents"] == 499
    saurma_names = {row["name"] for row in saurma.json()["items"]}
    assert "Šaurma" in saurma_names
    assert any(row["name"] == "Cepelinai su mėsa" for row in cepelinai.json()["items"])


def test_items_kebab_returns_cheapest_first_with_place() -> None:
    response = TestClient(app).get("/items", params={"q": "kebab", "sort": "price"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert items[0]["name"] == "Kebabas"
    assert items[0]["price_cents"] == 499
    assert isinstance(items[0]["price_cents"], int)
    assert items[0]["place"]["slug"] == "fabijoniskiu-valgykla"
    assert isinstance(items[0]["place"]["lat"], float)
    assert isinstance(items[0]["place"]["lng"], float)
    assert items[0]["place"]["name"]
    prices = [row["price_cents"] for row in items]
    assert prices == sorted(prices)


def test_items_seeded_name_literal_match() -> None:
    response = TestClient(app).get("/items", params={"q": "Kebabas pita"})
    assert response.status_code == 200
    names = [row["name"] for row in response.json()["items"]]
    assert names == ["Kebabas pita"]


def test_items_rejects_unknown_sort() -> None:
    response = TestClient(app).get("/items", params={"q": "kebab", "sort": "name"})
    assert response.status_code == 400


def test_items_geo_limits_to_radius() -> None:
    client = TestClient(app)
    old_town = client.get(
        "/items",
        params={
            "q": "kebab",
            "near": "54.6818,25.2874",
            "radius_m": 800,
        },
    )
    assert old_town.status_code == 200
    slugs = {row["place"]["slug"] for row in old_town.json()["items"]}
    assert "senamiescio-kebabine" in slugs
    assert "fabijoniskiu-valgykla" not in slugs
    assert all("distance_m" in row for row in old_town.json()["items"])


def test_items_near_without_radius_is_400() -> None:
    response = TestClient(app).get(
        "/items",
        params={"q": "kebab", "near": "54.68,25.27"},
    )
    assert response.status_code == 400


def test_items_vegan_pizza_drops_untagged_mixed_menu_rows() -> None:
    response = TestClient(app).get(
        "/items",
        params={"q": "pizza", "dietary": "vegan"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    names = {row["name"] for row in items}
    assert "Veganiška margarita" in names
    assert "Diavola" not in names
    assert all("vegan" in row["dietary_tags"] for row in items)


def test_items_conjunctive_dietary() -> None:
    response = TestClient(app).get(
        "/items",
        params={"dietary": "vegan,gluten_free"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for row in items:
        assert "vegan" in row["dietary_tags"]
        assert "gluten_free" in row["dietary_tags"]


def test_places_dietary_keeps_kitchens_with_verified_tags() -> None:
    response = TestClient(app).get(
        "/places",
        params={"bbox": VILNIUS_BBOX, "dietary": "vegan"},
    )
    assert response.status_code == 200
    slugs = {pin["slug"] for pin in response.json()["places"]}
    assert "saknys" in slugs
    assert "naujamiescio-picerija" in slugs
    assert "senamiescio-kebabine" not in slugs


def test_places_unknown_dietary_tag_is_400() -> None:
    response = TestClient(app).get(
        "/places",
        params={"bbox": VILNIUS_BBOX, "dietary": "keto"},
    )
    assert response.status_code == 400
