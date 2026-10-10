import time

import pytest
from argand import server
from fastapi.testclient import TestClient


@pytest.fixture
def review(monkeypatch):
    monkeypatch.setenv("ARGAND_PUBLIC_ORIGIN", "https://review.example")
    monkeypatch.setenv(
        "ARGAND_REVIEW_TOKEN", "test-only-token-with-at-least-32-characters"
    )
    monkeypatch.setenv("ARGAND_REVIEW_EXPIRES", str(int(time.time()) + 3600))
    return TestClient(server.app, base_url="https://review.example")


def test_gate_and_cookie(review):
    assert review.get("/").status_code == 401
    assert review.get("/api/config").status_code == 401
    assert (
        review.post(
            "/api/review/access",
            json={"token": "wrong"},
            headers={"origin": "https://review.example"},
        ).status_code
        == 403
    )
    r = review.post(
        "/api/review/access",
        json={"token": "test-only-token-with-at-least-32-characters"},
        headers={"origin": "https://review.example"},
    )
    assert r.status_code == 200
    assert "HttpOnly" in r.headers["set-cookie"] and "Secure" in r.headers["set-cookie"]
    assert review.get("/api/config").status_code == 200
    assert (
        review.post(
            "/api/practice/cube",
            json={"modulus": 2, "angle": 0},
            headers={"origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        review.post(
            "/api/practice/cube",
            json={"modulus": 2, "angle": 0},
            headers={"origin": "https://review.example"},
        ).status_code
        == 200
    )


def test_expiry_and_missing_config_fail_closed(review, monkeypatch):
    monkeypatch.setenv("ARGAND_REVIEW_EXPIRES", "0")
    assert review.get("/").status_code == 410
    monkeypatch.setenv("ARGAND_REVIEW_EXPIRES", str(int(time.time()) + 1000))
    monkeypatch.delenv("ARGAND_REVIEW_TOKEN")
    assert review.get("/api/config").status_code == 410


def test_host_and_bad_input(review):
    assert review.get("/", headers={"host": "other.example"}).status_code == 403
    assert (
        review.post(
            "/api/review/access",
            content="not json",
            headers={"origin": "https://review.example"},
        ).status_code
        == 403
    )
