import os
from io import BytesIO

from PIL import Image


def test_export_bitmap_without_jwt_responds_403(client):
    response = client.post("export_bitmap")
    assert response.status_code == 403


def test_export_bitmap_cbf(client, authentication_headers, dials_data):
    data = {
        "filename": os.fspath(
            dials_data("centroid_test_data", pathlib=True) / "centroid_0001.cbf"
        ),
        "image_index": 1,
        "format": "png",
        "binning": 4,
        "display": "image",
        "colour_scheme": "greyscale",
        "brightness": 10,
        "resolution_rings": {
            "show": True,
        },
    }
    response = client.post("export_bitmap", json=data, headers=authentication_headers)
    assert response.status_code == 200
    img = Image.open(BytesIO(response.content))
    assert img.size == (615, 631)


def test_export_bitmap_h5(client, authentication_headers, dials_data):
    data = {
        "filename": os.fspath(
            dials_data("vmxi_thaumatin", pathlib=True) / "image_15799_master.h5"
        ),
        "image_index": 10,
        "format": "png",
        "binning": 2,
    }
    response = client.post("export_bitmap", json=data, headers=authentication_headers)
    assert response.status_code == 200
    img = Image.open(BytesIO(response.content))
    assert img.size == (1034, 1081)
