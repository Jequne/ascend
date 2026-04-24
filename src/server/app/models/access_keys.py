from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .auth import AccessKeyStatus


class AccessKeys(Base):
    __tablename__ = "access_keys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    owner_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AccessKeyStatus.ACTIVE.value,
        index=True,
    )
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    secret_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    last_used_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_revoked(self) -> bool:
        return self.status == AccessKeyStatus.REVOKED.value or self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at <= datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        return self.status == AccessKeyStatus.ACTIVE.value and not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return f"AccessKeys(id={self.id!r}, name={self.name!r}, status={self.status!r})"

