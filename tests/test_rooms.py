def test_create_room(client, auth_headers):
    floor_resp = client.post(
        "/api/floors/",
        json={"name": "Room Test Floor", "floor_number": 20},
        headers=auth_headers,
    )
    floor_id = floor_resp.json()["id"]

    response = client.post(
        "/api/rooms/",
        json={"name": "201", "floor_id": floor_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "201"
    assert data["floor_id"] == floor_id
    assert data["waypoint_id"] is None


def test_get_rooms_returns_list(client):
    response = client.get("/api/rooms/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_rooms_by_text(client, auth_headers):
    floor_id = client.post(
        "/api/floors/",
        json={"name": "Search Floor", "floor_number": 21},
        headers=auth_headers,
    ).json()["id"]

    create_resp = client.post(
        "/api/rooms/",
        json={"name": "Teacher Room", "floor_id": floor_id},
        headers=auth_headers,
    )
    assert create_resp.status_code == 200

    resp = client.get("/api/rooms/search", params={"query": "Teacher"})
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()]
    assert "Teacher Room" in names


def test_search_rooms_by_id(client, auth_headers):
    floor_id = client.post(
        "/api/floors/",
        json={"name": "Search Floor 2", "floor_number": 22},
        headers=auth_headers,
    ).json()["id"]

    create_resp = client.post(
        "/api/rooms/",
        json={"name": "Unique Room", "floor_id": floor_id},
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    room_id = create_resp.json()["id"]

    resp = client.get("/api/rooms/search", params={"query": str(room_id)})
    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert room_id in ids


def test_get_rooms_building_filter_is_case_insensitive(client, auth_headers):
    floor_id = client.post(
        "/api/floors/",
        json={"name": "Building Floor", "floor_number": 23},
        headers=auth_headers,
    ).json()["id"]

    client.post(
        "/api/rooms/",
        json={"name": "106-b blok", "floor_id": floor_id},
        headers=auth_headers,
    )
    client.post(
        "/api/rooms/",
        json={"name": "106-C blok", "floor_id": floor_id},
        headers=auth_headers,
    )

    resp = client.get("/api/rooms/", params={"building": "B"})
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()]
    assert any("blok" in n.lower() and "-b" in n.lower() for n in names)
    assert all("-c" not in n.lower() for n in names)

