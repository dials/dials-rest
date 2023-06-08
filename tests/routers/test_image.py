import os
from io import BytesIO

import pytest
from fastapi import status
from PIL import Image


def test_export_bitmap_without_jwt_responds_403(client):
    response = client.post("export_bitmap")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_export_bitmap_file_not_found_responds_404(client, authentication_headers):
    data = {"filename": "/made/up/path.cbf"}
    response = client.post("export_bitmap", json=data, headers=authentication_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_export_bitmap_template_no_matching_file_responds_404(
    client, authentication_headers
):
    data = {"filename": "/made/up/path_#####.cbf"}
    response = client.post("export_bitmap", json=data, headers=authentication_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_export_bitmap_fails_to_understand_h5_data_file_responds_422(
    client, authentication_headers, dials_data
):
    data = {
        "filename": os.fspath(
            # this is the data file rather than NeXus file, so dials should
            # fail to understand
            dials_data("vmxi_thaumatin", pathlib=True)
            / "image_15799_data_000001.h5"
        ),
    }
    response = client.post("export_bitmap", json=data, headers=authentication_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_export_bitmap_fails_to_understand_text_file_responds_422(
    client, authentication_headers, tmp_path
):
    filename = tmp_path / "image_00001.cbf"
    filename.touch()
    for filename in {filename, tmp_path / "image_#####.cbf"}:
        data = {"filename": os.fspath(filename)}
        response = client.post(
            "export_bitmap", json=data, headers=authentication_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("filename", ["centroid_0001.cbf", "centroid_####.cbf"])
def test_export_bitmap_cbf(filename, client, authentication_headers, dials_data):
    data = {
        "filename": os.fspath(
            dials_data("centroid_test_data", pathlib=True) / filename
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
