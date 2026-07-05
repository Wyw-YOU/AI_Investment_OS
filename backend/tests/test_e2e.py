"""End-to-end integration tests — smoke test the full API surface."""


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestStockAPI:
    def test_get_stock(self, client):
        resp = client.get("/api/stocks/600519")
        assert resp.status_code == 200
        assert resp.json()["stock_code"] == "600519"

    def test_hot_stocks(self, client):
        resp = client.get("/api/stocks/hot")
        assert resp.status_code == 200


class TestPortfolioAPI:
    def test_full_crud(self, client):
        resp = client.post("/api/portfolio/?name=TestP")
        assert resp.status_code == 200
        pid = resp.json()["id"]

        resp = client.get("/api/portfolio/")
        assert resp.status_code == 200

        resp = client.get(f"/api/portfolio/{pid}")
        assert resp.status_code == 200

        resp = client.delete(f"/api/portfolio/{pid}")
        assert resp.status_code == 200

    def test_candidate_pool(self, client):
        resp = client.post("/api/portfolio/?name=PoolTest")
        pid = resp.json()["id"]

        resp = client.post(f"/api/portfolio/{pid}/pool?stock_code=600519")
        assert resp.status_code == 200
        assert "600519" in resp.json()["candidate_pool"]

        resp = client.delete(f"/api/portfolio/{pid}/pool/600519")
        assert resp.status_code == 200

    def test_risk_score(self, client):
        resp = client.post("/api/portfolio/?name=RiskTest")
        pid = resp.json()["id"]

        resp = client.get(f"/api/portfolio/{pid}/risk")
        assert resp.status_code == 200
        assert "risk_score" in resp.json()


class TestAlertAPI:
    def test_alerts_list(self, client):
        resp = client.get("/api/alerts/")
        assert resp.status_code == 200
        assert "alerts" in resp.json()

    def test_unread_alerts(self, client):
        resp = client.get("/api/alerts/unread")
        assert resp.status_code == 200
        assert "count" in resp.json()


class TestAuthFlow:
    def test_register_login_me(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "e2e_user",
            "password": "password123",
        })
        assert resp.status_code == 200
        token = resp.json()["token"]

        resp = client.post("/api/auth/login", json={
            "username": "e2e_user",
            "password": "password123",
        })
        assert resp.status_code == 200

        resp = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == "e2e_user"
