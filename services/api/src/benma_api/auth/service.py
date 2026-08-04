"""Development phone authentication and opaque device sessions."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import phonenumbers
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import Account, AuthIdentity, AuthSession
from benma_api.db.session import get_db
from benma_api.errors import AuthenticationError

bearer = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_phone(number: str) -> str:
    try:
        parsed = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException as exc:
        raise AuthenticationError("phone number must be a valid international number") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise AuthenticationError("phone number is not valid")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def create_dev_session(
    db: Session, settings: Settings, phone_number: str
) -> tuple[Account, AuthSession, str]:
    if not settings.dev_auth_enabled:
        raise AuthenticationError("development authentication is disabled")
    phone = normalize_phone(phone_number)
    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.method == "phone", AuthIdentity.phone_e164 == phone
        )
    )
    account: Account
    if identity is None:
        account = Account()
        db.add(account)
        db.flush()
        identity = AuthIdentity(account_id=account.id, method="phone", phone_e164=phone)
        db.add(identity)
    else:
        found_account = db.get(Account, identity.account_id)
        if found_account is None:
            raise AuthenticationError("authentication identity has no account")
        account = found_account
    token = secrets.token_urlsafe(48)
    auth_session = AuthSession(
        account_id=account.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_ttl_days),
    )
    db.add(auth_session)
    db.commit()
    return account, auth_session, token


@dataclass(frozen=True, slots=True)
class AuthContext:
    account: Account
    session: AuthSession

    @property
    def account_id(self) -> uuid.UUID:
        return self.account.id


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise AuthenticationError("a bearer token is required")
    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(credentials.credentials))
    )
    now = datetime.now(UTC)
    if auth_session is None or auth_session.revoked_at is not None:
        raise AuthenticationError("the session is invalid or expired")
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        raise AuthenticationError("the session is invalid or expired")
    account = db.get(Account, auth_session.account_id)
    if account is None or account.status != "active":
        raise AuthenticationError("the account is unavailable")
    return AuthContext(account=account, session=auth_session)


def revoke_session(db: Session, auth: AuthContext) -> None:
    auth.session.revoked_at = datetime.now(UTC)
    db.commit()
