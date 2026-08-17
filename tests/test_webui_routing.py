"""Webui routing behavior tests: unmatched paths redirect to the SPA home.

The frontend is a hash router (#/xxx in the URL fragment), which the
browser never sends to the server, so the server only owns the registered
API routes, "/" and the static assets. Everything else must 302 back to
"/" (loop-guarded when the SPA build is missing).
"""

import os

import pytest
from fastapi.testclient import TestClient

from module.webui.api import create_api_app

DIST_INDEX = os.path.join("webapp-tauri", "dist", "index.html")


@pytest.fixture
def client():
    # No lifespan: routing behavior only, no State/process side effects.
    test_client = TestClient(create_api_app())
    yield test_client
    test_client.close()


def test_unknown_path_redirects_home(client):
    response = client.get("/nonexistent-xyz-123", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_deep_path_redirects_home(client):
    response = client.get("/deep/link/page", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_api_typo_redirects_home(client):
    # Policy: all non-specified paths go home, including API typos.
    response = client.get("/api/status", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_registered_route_still_works(client):
    # /i18n/{lang} needs no lifespan state and always answers 200.
    response = client.get("/i18n/zh-CN")
    assert response.status_code == 200


def test_root_never_redirect_loops(client):
    # When dist is built, "/" serves the SPA; when it is not, "/" must
    # return the JSON 404 rather than redirect to itself.
    response = client.get("/", follow_redirects=False)
    if os.path.isfile(DIST_INDEX):
        assert response.status_code == 200
    else:
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}


def test_hash_fragment_is_client_side(client):
    # The browser never sends the #fragment; the server only sees "/"
    # and the SPA router handles the hash. Pin that the server treats the
    # path without the fragment as the SPA root.
    response = client.get("/", follow_redirects=False)
    if os.path.isfile(DIST_INDEX):
        assert response.status_code == 200
    else:
        assert response.status_code == 404
