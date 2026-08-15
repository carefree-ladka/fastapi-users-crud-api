"""Data access for persisted refresh tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Store, look up, and revoke refresh tokens by their ``jti``."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, jti: str, user_id: int, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at, revoked=False)
        self._db.add(token)
        self._db.commit()
        self._db.refresh(token)
        return token

    def get(self, jti: str) -> RefreshToken | None:
        return self._db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def revoke(self, jti: str) -> None:
        self._db.execute(update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True))
        self._db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        self._db.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        )
        self._db.commit()
