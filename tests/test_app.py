"""Drive the shipped HTTP entry — the real FastAPI app, not a stand-in."""

from fastapi.testclient import TestClient

from kurpaest.app import SERVICE_NAME, SERVICE_STATUS_OK, SITE, app, root


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
