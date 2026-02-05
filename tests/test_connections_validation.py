def create_floor(client, headers, floor_number=1, name="1-qavat"):
    resp = client.post(
        "/api/floors/",
        json={"name": name, "floor_number": floor_number},
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()


def create_waypoint(client, headers, floor_id, waypoint_id, x=0, y=0, wp_type="hallway", label=None):
    payload = {
        "id": waypoint_id,
        "floor_id": floor_id,
        "x": x,
        "y": y,
        "type": wp_type,
        "label": label,
    }
    resp = client.post("/api/waypoints/", json=payload, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_create_connection_rejects_non_positive_distance(client, auth_headers):
    floor = create_floor(client, auth_headers)
    create_waypoint(client, auth_headers, floor["id"], "wp-a")
    create_waypoint(client, auth_headers, floor["id"], "wp-b")

    resp = client.post(
        "/api/waypoints/connections",
        json={"from_waypoint_id": "wp-a", "to_waypoint_id": "wp-b", "distance": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_connection_rejects_self_loop(client, auth_headers):
    floor = create_floor(client, auth_headers)
    create_waypoint(client, auth_headers, floor["id"], "wp-a")

    resp = client.post(
        "/api/waypoints/connections",
        json={"from_waypoint_id": "wp-a", "to_waypoint_id": "wp-a", "distance": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_create_connection_rejects_duplicate_in_reverse_direction(client, auth_headers):
    floor = create_floor(client, auth_headers)
    create_waypoint(client, auth_headers, floor["id"], "wp-a")
    create_waypoint(client, auth_headers, floor["id"], "wp-b")

    ok = client.post(
        "/api/waypoints/connections",
        json={"from_waypoint_id": "wp-a", "to_waypoint_id": "wp-b", "distance": 10},
        headers=auth_headers,
    )
    assert ok.status_code == 200

    dup = client.post(
        "/api/waypoints/connections",
        json={"from_waypoint_id": "wp-b", "to_waypoint_id": "wp-a", "distance": 10},
        headers=auth_headers,
    )
    assert dup.status_code == 409


def test_create_connections_batch_rejects_duplicates_in_request(client, auth_headers):
    floor = create_floor(client, auth_headers)
    create_waypoint(client, auth_headers, floor["id"], "wp-a")
    create_waypoint(client, auth_headers, floor["id"], "wp-b")

    resp = client.post(
        "/api/waypoints/connections/batch",
        json=[
            {"from_waypoint_id": "wp-a", "to_waypoint_id": "wp-b", "distance": 10},
            {"from_waypoint_id": "wp-b", "to_waypoint_id": "wp-a", "distance": 10},
        ],
        headers=auth_headers,
    )
    assert resp.status_code == 400

