import pytest
from fastapi.testclient import TestClient

JWT_SECRET = "FooBar"


def pytest_configure(config):
    if not config.pluginmanager.hasplugin("dials_data"):

        @pytest.fixture(scope="session")
        def dials_data():
            pytest.skip("This test requires the dials_data package to be installed")

        globals()["dials_data"] = dials_data


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)
    from dials_rest.main import app

    return TestClient(app)


@pytest.fixture
def access_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)

    from dials_rest.auth import create_access_token

    return create_access_token(data={})


@pytest.fixture
def authentication_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}
