def test_create_room_with_unknown_waypoint_returns_404(client, auth_headers):
    floor_resp = client.post(
        "/api/floors/",
        json={"name": "Floor 1", "floor_number": 1},
        headers=auth_headers,
    )
    floor_id = floor_resp.json()["id"]

    resp = client.post(
        "/api/rooms/",
        json={"name": "Some Room", "floor_id": floor_id, "waypoint_id": "missing-wp"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Waypoint not found"


def test_create_room_with_waypoint_floor_mismatch_returns_400(client, auth_headers):
    floor1 = client.post(
        "/api/floors/",
        json={"name": "Floor 1", "floor_number": 1},
        headers=auth_headers,
    ).json()
    floor2 = client.post(
        "/api/floors/",
        json={"name": "Floor 2", "floor_number": 2},
        headers=auth_headers,
    ).json()

    wp = client.post(
        "/api/waypoints/",
        json={"id": "wp-room-1", "floor_id": floor1["id"], "x": 10, "y": 20, "type": "room"},
        headers=auth_headers,
    ).json()

    resp = client.post(
        "/api/rooms/",
        json={"name": "Some Room", "floor_id": floor2["id"], "waypoint_id": wp["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Waypoint does not belong to the room floor"


def test_create_room_sets_floor_from_waypoint_when_floor_missing(client, auth_headers):
    floor = client.post(
        "/api/floors/",
        json={"name": "Floor 1", "floor_number": 1},
        headers=auth_headers,
    ).json()

    wp = client.post(
        "/api/waypoints/",
        json={"id": "wp-room-2", "floor_id": floor["id"], "x": 10, "y": 20, "type": "room"},
        headers=auth_headers,
    ).json()

    resp = client.post(
        "/api/rooms/",
        json={"name": "Some Room", "waypoint_id": wp["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["floor_id"] == floor["id"]
    assert resp.json()["waypoint_id"] == wp["id"]

