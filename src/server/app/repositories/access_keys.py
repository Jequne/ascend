from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from ..models.access_keys import AccessKeys
from ..models.auth import AccessKeyStatus


class AccessKeyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, key_id: str) -> AccessKeys | None:
        statement: Select[tuple[AccessKeys]] = select(AccessKeys).where(AccessKeys.id == key_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_secret_hash(self, secret_hash: str) -> AccessKeys | None:
        statement: Select[tuple[AccessKeys]] = select(AccessKeys).where(
            AccessKeys.secret_hash == secret_hash
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
    ) -> list[AccessKeys]:
        statement = select(AccessKeys)

        if owner_type is not None:
            statement = statement.where(AccessKeys.owner_type == owner_type)
        if owner_id is not None:
            statement = statement.where(AccessKeys.owner_id == owner_id)
        if status is not None:
            statement = statement.where(AccessKeys.status == status)

        statement = statement.order_by(desc(AccessKeys.created_at))
        return list(self.db.execute(statement).scalars().all())

    def add(self, access_key: AccessKeys) -> AccessKeys:
        self.db.add(access_key)
        self.db.commit()
        self.db.refresh(access_key)
        return access_key

    def save(self, access_key: AccessKeys) -> AccessKeys:
        self.db.add(access_key)
        self.db.commit()
        self.db.refresh(access_key)
        return access_key

    def revoke(self, access_key: AccessKeys, revoked_at: datetime | None = None) -> AccessKeys:
        access_key.status = AccessKeyStatus.REVOKED.value
        access_key.revoked_at = revoked_at or datetime.now(timezone.utc)
        return self.save(access_key)

    def touch(self, access_key: AccessKeys, *, ip_address: str | None = None) -> AccessKeys:
        access_key.last_used_at = datetime.now(timezone.utc)
        access_key.last_used_ip = ip_address
        access_key.usage_count += 1
        return self.save(access_key)