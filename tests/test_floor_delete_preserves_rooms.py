def test_delete_floor_preserves_rooms_and_nulls_floor_id(client, auth_headers):
    floor_resp = client.post(
        "/api/floors/",
        json={"name": "Floor 1", "floor_number": 1},
        headers=auth_headers,
    )
    floor_id = floor_resp.json()["id"]

    room_resp = client.post(
        "/api/rooms/",
        json={"name": "Room A", "floor_id": floor_id},
        headers=auth_headers,
    )
    assert room_resp.status_code == 200
    room_id = room_resp.json()["id"]

    delete_resp = client.delete(f"/api/floors/{floor_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    # Room still exists but has no floor assigned anymore
    get_room = client.get(f"/api/rooms/{room_id}")
    assert get_room.status_code == 200
    data = get_room.json()
    assert data["floor_id"] is None
    assert data["waypoint_id"] is None

