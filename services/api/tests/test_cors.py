from __future__ import annotations

import pytest
from conftest import ApiClient
from pydantic import ValidationError

from benma_api.app import create_app
from benma_api.config import Settings


@pytest.fixture
def settings(settings: Settings) -> Settings:
    # Exercise actual development defaults without inheriting a local origin allowlist.
    return settings.model_copy(update={"environment": "development", "cors_allowed_origins": []})


def preflight(
    client: ApiClient,
    origin: str,
    path: str = "/v1/dev/auth",
    *,
    method: str = "POST",
    headers: str = "content-type",
):
    return client.request(
        "OPTIONS",
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )


@pytest.mark.parametrize("origin", ["http://localhost:8081", "http://127.0.0.1:8081"])
@pytest.mark.parametrize(
    "path,method,headers",
    [
        ("/v1/dev/auth", "POST", "content-type"),
        ("/v1/me", "GET", "authorization"),
        ("/v1/utterances", "POST", "authorization,content-type"),
        ("/v1/conversations/c/user-turns/stream", "POST", "authorization,content-type"),
        ("/v1/auth/session", "DELETE", "authorization"),
    ],
)
def test_localhost_preflight(client, origin, path, method, headers):
    response = preflight(client, origin, path, method=method, headers=headers)
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert set(response.headers["Access-Control-Allow-Methods"].split(", ")) == {
        "GET",
        "POST",
        "DELETE",
    }
    allowed_headers = response.headers["Access-Control-Allow-Headers"].lower().split(", ")
    assert all(header in allowed_headers for header in headers.split(","))
    assert "Origin" in response.headers["Vary"]
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_configured_lan_origin_from_environment(monkeypatch):
    origin = "http://192.168.68.59:8081"
    monkeypatch.setenv("BENMA_CORS_ALLOWED_ORIGINS", f'["{origin}"]')
    settings = Settings(_env_file=None, environment="development", dev_auth_enabled=False)
    client = ApiClient(create_app(settings))
    assert preflight(client, origin).status_code == 200
    assert preflight(client, "http://localhost:8081").status_code == 200
    assert preflight(client, "http://192.168.68.60:8081").status_code == 400
    # Allowing CORS cannot enable a disabled development login route.
    response = client.post(
        "/v1/dev/auth", headers={"Origin": origin}, json={"phone_number": "+12025550123"}
    )
    assert response.status_code == 404
    assert response.headers["Access-Control-Allow-Origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "https://arbitrary.example",
        "http://localhost:8082",
        "http://localhost.evil.example:8081",
        "http://192.168.68.59:8081",
        "null",
    ],
)
def test_unconfigured_origin_is_denied(client, origin):
    response = preflight(client, origin)
    assert response.status_code == 400
    assert "Access-Control-Allow-Origin" not in response.headers
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200  # CORS is browser enforcement, not route authorization.
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.parametrize("method,headers", [("PUT", "authorization"), ("POST", "x-custom-header")])
def test_unneeded_method_or_header_is_denied(client, method, headers):
    response = preflight(client, "http://localhost:8081", method=method, headers=headers)
    assert response.status_code == 400


@pytest.mark.parametrize("origin", [None, "http://localhost:8081"])
def test_browser_and_native_auth_still_require_bearer_token(client, origin):
    headers = {"Origin": origin} if origin else {}
    login = client.post("/v1/dev/auth", headers=headers, json={"phone_number": "+12025550123"})
    assert login.status_code == 200
    token = login.json()["token"]
    assert token
    if origin:
        assert login.headers["Access-Control-Allow-Origin"] == origin
        assert login.headers["Access-Control-Expose-Headers"] == "Server-Timing"
    else:
        assert "Access-Control-Allow-Origin" not in login.headers
    assert "Access-Control-Allow-Credentials" not in login.headers
    for auth in ({}, {"Authorization": "Bearer invalid"}):
        response = client.get("/v1/me", headers={**headers, **auth})
        assert response.status_code == 401
        if origin:
            assert response.headers["Access-Control-Allow-Origin"] == origin
    authenticated = {**headers, "Authorization": f"Bearer {token}"}
    me = client.get("/v1/me", headers=authenticated)
    assert me.status_code == 200
    assert me.json()["id"] == login.json()["account_id"]
    assert client.delete("/v1/auth/session", headers=authenticated).status_code == 204
    assert client.get("/v1/me", headers=authenticated).status_code == 401
    invalid_login = client.post("/v1/dev/auth", headers=headers, json={"phone_number": "bad"})
    assert invalid_login.status_code == 422
    if origin:
        assert invalid_login.headers["Access-Control-Allow-Origin"] == origin


@pytest.mark.parametrize("environment", ["test", "production"])
def test_non_development_has_no_implicit_origins(environment):
    settings = Settings(
        _env_file=None, environment=environment, dev_auth_enabled=False, cors_allowed_origins=[]
    )
    assert settings.effective_cors_origins == []
    client = ApiClient(create_app(settings))
    for origin in ("http://localhost:8081", "http://127.0.0.1:8081", "https://web.example"):
        response = preflight(client, origin)
        assert response.status_code == 400
        assert "Access-Control-Allow-Origin" not in response.headers
    assert client.get("/health").status_code == 200


def test_production_requires_explicit_origin_and_keeps_dev_auth_closed():
    origin = "https://web.example"
    client = ApiClient(
        create_app(
            Settings(
                _env_file=None,
                environment="production",
                dev_auth_enabled=False,
                cors_allowed_origins=[origin],
            )
        )
    )
    assert (
        preflight(client, origin, "/v1/me", method="GET", headers="authorization").status_code
        == 200
    )
    assert preflight(client, "http://localhost:8081").status_code == 400
    response = client.get("/health", headers={"Origin": origin})
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert "Access-Control-Allow-Credentials" not in response.headers
    assert "Access-Control-Expose-Headers" not in response.headers
    assert client.post("/v1/dev/auth", json={"phone_number": "+12025550123"}).status_code == 404


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.com",
        "http://localhost:8081/login",
        "http://localhost:8081?x=1",
        "http://localhost:8081#fragment",
        "http://user:password@localhost:8081",
        "file:///tmp/app",
    ],
)
def test_config_rejects_wildcards_and_non_origins(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_allowed_origins=[origin])


def test_config_normalizes_origins_without_duplicate_defaults():
    settings = Settings(
        _env_file=None,
        environment="development",
        cors_allowed_origins=["http://localhost:8081/", "https://WEB.example:443/"],
    )
    assert settings.effective_cors_origins == [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "https://web.example",
    ]
