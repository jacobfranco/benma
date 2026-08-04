from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from conftest import ApiClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.app import create_app
from benma_api.config import Settings
from benma_api.db.models import AuthIdentity, AuthSession


def test_health_requires_no_auth(client: ApiClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_dev_auth_normalizes_phone_and_hashes_opaque_token(
    client: ApiClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post("/v1/dev/auth", json={"phone_number": "+1 202-555-0123"})
    assert response.status_code == 200
    token = response.json()["token"]
    assert len(token) >= 64
    with session_factory() as db:
        identity = db.scalar(select(AuthIdentity))
        auth_session = db.scalar(select(AuthSession))
        assert identity is not None and identity.phone_e164 == "+12025550123"
        assert auth_session is not None
        assert auth_session.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token != auth_session.token_hash


def test_dev_auth_reuses_account(client: ApiClient) -> None:
    first = client.post("/v1/dev/auth", json={"phone_number": "+12025550123"}).json()
    second = client.post("/v1/dev/auth", json={"phone_number": "+12025550123"}).json()
    assert first["account_id"] == second["account_id"]
    assert first["token"] != second["token"]


def test_dev_auth_route_is_absent_when_disabled() -> None:
    client = ApiClient(create_app(Settings(environment="test", database_url="sqlite://")))
    response = client.post("/v1/dev/auth", json={"phone_number": "+12025550123"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"]


def test_token_validity_and_revocation(client: ApiClient, auth_header: dict[str, str]) -> None:
    assert client.get("/v1/me", headers=auth_header).status_code == 200
    assert client.delete("/v1/auth/session", headers=auth_header).status_code == 204
    response = client.get("/v1/me", headers=auth_header)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


def test_expired_token_is_rejected(
    client: ApiClient,
    auth_header: dict[str, str],
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        auth_session = db.scalar(select(AuthSession))
        assert auth_session is not None
        auth_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    response = client.get("/v1/me", headers=auth_header)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


def test_invalid_token_is_stable_auth_error(client: ApiClient) -> None:
    response = client.get("/v1/me", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401
    assert response.json()["error"]["request_id"]


def test_production_refuses_dev_auth() -> None:
    with pytest.raises(ValidationError, match="development authentication"):
        Settings(environment="production", dev_auth_enabled=True)


def test_live_provider_configuration_never_falls_back() -> None:
    with pytest.raises(ValidationError, match="OPENAI"):
        Settings(perception_provider="openai", openai_api_key=None)
    with pytest.raises(ValidationError, match="Azure"):
        Settings(assessment_provider="azure")
