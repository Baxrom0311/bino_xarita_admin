def test_refresh_issues_new_jwt_and_still_allows_admin_access(client):
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123456"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    refresh_resp = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.json()["access_token"]
    assert isinstance(new_token, str) and new_token

    # New token can access admin endpoint
    create_floor_resp = client.post(
        "/api/floors/",
        json={"name": "Refresh JWT Floor", "floor_number": 77},
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert create_floor_resp.status_code == 200


def test_refresh_accepts_legacy_admin_token(client, auth_headers):
    refresh_resp = client.post("/api/auth/refresh", headers=auth_headers)
    assert refresh_resp.status_code == 200
    assert isinstance(refresh_resp.json()["access_token"], str)


def test_refresh_rejects_invalid_token(client):
    resp = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert resp.status_code == 401


def test_refresh_rejects_non_admin_jwt(client):
    from datetime import timedelta
    from app.core.security import create_access_token

    token = create_access_token(
        data={"sub": "user1", "role": "user"},
        expires_delta=timedelta(minutes=5),
    )
    resp = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
