import os
from unittest import mock

import pytest


@pytest.mark.parametrize("filename", ["centroid_0001.cbf", "centroid_####.cbf"])
def test_find_spots_cbf(filename, client, authentication_headers, dials_data):
    data = {
        "filename": os.fspath(
            dials_data("centroid_test_data", pathlib=True) / filename
        ),
        "scan_range": (1, 1),
        "d_min": 3.5,
    }
    response = client.post("find_spots", json=data, headers=authentication_headers)
    assert response.status_code == 200
    assert response.json() == {
        "n_spots_4A": 36,
        "n_spots_no_ice": 44,
        "n_spots_total": 49,
        "total_intensity": 56848.0,
        "d_min_distl_method_1": mock.ANY,
        "d_min_distl_method_2": mock.ANY,
        "estimated_d_min": mock.ANY,
        "noisiness_method_1": mock.ANY,
        "noisiness_method_2": mock.ANY,
    }


def test_find_spots_h5(client, authentication_headers, dials_data):
    data = {
        "filename": os.fspath(
            dials_data("vmxi_thaumatin", pathlib=True) / "image_15799_master.h5"
        ),
        "scan_range": (1, 1),
    }
    response = client.post("find_spots", json=data, headers=authentication_headers)
    assert response.status_code == 200
    assert response.json() == {
        "n_spots_4A": 21,
        "n_spots_no_ice": 41,
        "n_spots_total": 47,
        "total_intensity": 7386.0,
        "d_min_distl_method_1": mock.ANY,
        "d_min_distl_method_2": mock.ANY,
        "estimated_d_min": mock.ANY,
        "noisiness_method_1": mock.ANY,
        "noisiness_method_2": mock.ANY,
    }
