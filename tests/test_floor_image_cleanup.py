import io
import os

from PIL import Image


def _make_png_bytes(color=(255, 0, 0)):
    img = Image.new("RGB", (10, 10), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_floor_image_reupload_deletes_old_file(client, auth_headers):
    floor_resp = client.post(
        "/api/floors/",
        json={"name": "Floor 1", "floor_number": 1},
        headers=auth_headers,
    )
    floor_id = floor_resp.json()["id"]

    # First upload
    data1 = _make_png_bytes(color=(255, 0, 0))
    resp1 = client.post(
        f"/api/floors/{floor_id}/upload-image",
        files={"file": ("a.png", data1, "image/png")},
        headers=auth_headers,
    )
    assert resp1.status_code == 200
    url1 = resp1.json()["image_url"]
    file1 = os.path.join("uploads", os.path.basename(url1))
    assert os.path.exists(file1)

    # Second upload
    data2 = _make_png_bytes(color=(0, 255, 0))
    resp2 = client.post(
        f"/api/floors/{floor_id}/upload-image",
        files={"file": ("b.png", data2, "image/png")},
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    url2 = resp2.json()["image_url"]
    file2 = os.path.join("uploads", os.path.basename(url2))
    assert os.path.exists(file2)

    # Old file should be removed
    assert not os.path.exists(file1)

    # Cleanup new file (best-effort)
    if os.path.exists(file2):
        os.remove(file2)

