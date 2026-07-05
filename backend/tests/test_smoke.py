"""Smoke tests for Phase 0 foundation."""

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_auth_me_endpoint(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_stock_endpoint(client):
    response = client.get("/api/stocks/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "600519"


def test_portfolio_list(client):
    response = client.get("/api/portfolio/")
    assert response.status_code == 200


def test_alerts_list(client):
    response = client.get("/api/alerts/")
    assert response.status_code == 200
