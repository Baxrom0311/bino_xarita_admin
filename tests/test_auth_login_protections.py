def test_login_rate_limit_returns_429(client):
    from app.core.config import settings

    # Keep brute-force disabled for this test; focus on rate limiting
    settings.LOGIN_MAX_FAILED_ATTEMPTS = 10_000
    settings.LOGIN_RATE_LIMIT_PER_MINUTE = 3

    headers = {"X-Forwarded-For": "10.10.10.10"}
    for _ in range(3):
        r = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
            headers=headers,
        )
        assert r.status_code == 401

    limited = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
        headers=headers,
    )
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers


def test_login_bruteforce_lockout_returns_429(client):
    from app.core.config import settings

    # Keep rate limit high for this test; focus on lockout
    settings.LOGIN_RATE_LIMIT_PER_MINUTE = 10_000
    settings.LOGIN_MAX_FAILED_ATTEMPTS = 3
    settings.LOGIN_FAILURE_WINDOW_SECONDS = 60
    settings.LOGIN_LOCK_SECONDS = 60

    headers = {"X-Forwarded-For": "10.10.10.11"}
    for _ in range(3):
        r = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
            headers=headers,
        )
        assert r.status_code == 401

    locked = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
        headers=headers,
    )
    assert locked.status_code == 429
    assert "Retry-After" in locked.headers

