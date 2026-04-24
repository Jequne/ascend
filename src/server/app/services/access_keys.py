from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..config import settings
from ..models.access_keys import AccessKeys
from ..models.auth import AccessKeyStatus, AuthContext, AuthMethod, PrincipalType, normalize_scopes
from ..repositories.access_keys import AccessKeyRepository
from ..schemas.auth import AccessKeyCreateRequest, AccessKeyRead, AccessKeyRotateResponse, IssuedAccessKey
from .exceptions import (
    AccessKeyExpiredError,
    AccessKeyFormatError,
    AccessKeyInactiveError,
    AccessKeyNotFoundError,
    AuthenticationError,
)
from .hashers import ApiKeyCodec, ParsedApiKey, SecretHasher


class AccessKeyService:
    def __init__(
        self,
        db: Session,
        *,
        settings_obj=settings,
        repository: AccessKeyRepository | None = None,
        hasher: SecretHasher | None = None,
        codec: ApiKeyCodec | None = None,
    ):
        self.db = db
        self.settings = settings_obj
        self.repository = repository or AccessKeyRepository(db)
        self.hasher = hasher or SecretHasher(settings_obj.auth_api_key_hash_iterations)
        self.codec = codec or ApiKeyCodec(settings_obj.auth_api_key_prefix)

    def _default_expiration(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=self.settings.auth_api_key_default_ttl_days)

    def _build_model(self, request: AccessKeyCreateRequest) -> tuple[AccessKeys, str]:
        key_id = uuid4().hex
        secret = uuid4().hex
        salt, secret_hash = self.hasher.create_secret_hash(secret)

        access_key = AccessKeys(
            id=key_id,
            name=request.name,
            description=request.description,
            owner_type=request.owner_type,
            owner_id=request.owner_id,
            status=AccessKeyStatus.ACTIVE.value,
            scopes=normalize_scopes(request.scopes),
            secret_hash=secret_hash,
            secret_salt=salt,
            token_prefix=key_id[:8],
            version=1,
            issued_at=datetime.now(timezone.utc),
            expires_at=request.expires_at or self._default_expiration(),
        )
        return access_key, secret

    def issue_access_key(self, request: AccessKeyCreateRequest) -> IssuedAccessKey:
        access_key, secret = self._build_model(request)
        saved = self.repository.add(access_key)
        return IssuedAccessKey(
            access_key=self.codec.issue(saved.id, secret),
            secret=secret,
            key=AccessKeyRead.model_validate(saved),
        )

    def list_access_keys(
        self,
        *,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
    ) -> list[AccessKeyRead]:
        records = self.repository.list(owner_type=owner_type, owner_id=owner_id, status=status)
        return [AccessKeyRead.model_validate(record) for record in records]

    def _parse(self, access_key_value: str) -> ParsedApiKey:
        try:
            return self.codec.parse(access_key_value)
        except ValueError as exc:
            raise AccessKeyFormatError(str(exc)) from exc

    def authenticate(self, access_key_value: str, *, ip_address: str | None = None) -> AuthContext:
        parsed = self._parse(access_key_value)
        access_key = self.repository.get_by_id(parsed.key_id)

        if access_key is None:
            raise AccessKeyNotFoundError("access key not found")
        if access_key.status != AccessKeyStatus.ACTIVE.value or access_key.is_revoked:
            raise AccessKeyInactiveError("access key is not active")
        if access_key.is_expired:
            raise AccessKeyExpiredError("access key is expired")
        if not self.hasher.verify(parsed.secret, access_key.secret_salt, access_key.secret_hash):
            raise AuthenticationError("access key secret mismatch")

        self.repository.touch(access_key, ip_address=ip_address)
        return AuthContext(
            principal_type=PrincipalType.ACCESS_KEY,
            principal_id=access_key.id,
            auth_method=AuthMethod.API_KEY,
            scopes=access_key.scopes,
            key_id=access_key.id,
            issued_at=access_key.issued_at,
            expires_at=access_key.expires_at,
            metadata={
                "name": access_key.name,
                "owner_type": access_key.owner_type or "",
                "owner_id": access_key.owner_id or "",
            },
        )

    def revoke_access_key(self, key_id: str) -> AccessKeyRead:
        access_key = self.repository.get_by_id(key_id)
        if access_key is None:
            raise AccessKeyNotFoundError("access key not found")
        revoked = self.repository.revoke(access_key)
        return AccessKeyRead.model_validate(revoked)

    def rotate_access_key(self, key_id: str) -> AccessKeyRotateResponse:
        access_key = self.repository.get_by_id(key_id)
        if access_key is None:
            raise AccessKeyNotFoundError("access key not found")

        secret = uuid4().hex
        salt, secret_hash = self.hasher.create_secret_hash(secret)
        access_key.secret_salt = salt
        access_key.secret_hash = secret_hash
        access_key.version += 1
        access_key.status = AccessKeyStatus.ACTIVE.value
        access_key.revoked_at = None
        access_key.expires_at = access_key.expires_at or self._default_expiration()
        refreshed = self.repository.save(access_key)
        return AccessKeyRotateResponse(
            access_key=self.codec.issue(refreshed.id, secret),
            secret=secret,
            key=AccessKeyRead.model_validate(refreshed),
        )