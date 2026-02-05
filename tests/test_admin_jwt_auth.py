def test_admin_jwt_can_access_admin_endpoints(client):
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123456"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    jwt_headers = {"Authorization": f"Bearer {token}"}
    create_floor_resp = client.post(
        "/api/floors/",
        json={"name": "JWT Floor", "floor_number": 99},
        headers=jwt_headers,
    )
    assert create_floor_resp.status_code == 200
