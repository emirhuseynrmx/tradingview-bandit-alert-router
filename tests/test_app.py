from litestar.testing import TestClient

from tradingview_bandit_router.app import app


def test_health() -> None:
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}


def test_alert_endpoint_validates_payload() -> None:
    client = TestClient(app)
    response = client.post("/v1/alerts", json={"alert_id": "short"})

    assert response.status_code == 400
