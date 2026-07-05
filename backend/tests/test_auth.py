"""Tests for JWT authentication."""
import pytest
from app.core.auth import hash_password, verify_password, create_token, decode_token


class TestPassword:
    def test_hash_and_verify(self):
        hashed = hash_password("test123")
        assert verify_password("test123", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("test123")
        h2 = hash_password("test123")
        assert h1 != h2


class TestToken:
    def test_create_and_decode(self):
        token = create_token("user-123")
        user_id = decode_token(token)
        assert user_id == "user-123"

    def test_invalid_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_token("invalid.token.here")


class TestAuthEndpoints:
    def test_register_and_login(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "test123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data

        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123456",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "username": "testuser2",
            "password": "test123456",
        })
        resp = client.post("/api/auth/login", json={
            "username": "testuser2",
            "password": "wrong",
        })
        assert resp.status_code == 401
