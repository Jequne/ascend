import pytest

from datetime import datetime, timezone, timedelta

from ...domain import ApiKey, ApiKeyStatus



def test_max_active_sessions_more_than_expected() -> None:
    with pytest.raises(ValueError):
        ApiKey(
            kid="kid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            max_active_sessions=ApiKey.MAX_ACTIVE_SESSIONS_LIMIT + 1,
            key_hash="key_hash",
            label="label"
        )


def test_max_active_sessions_less_than_one() -> None:
    with pytest.raises(ValueError):
        ApiKey(
            kid="kid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            max_active_sessions=0,
            key_hash="key_hash",
            label="label"
        )


def test_current_status_when_already_expired_expect_revoked() -> None:
    # Если апи ключ завершился ЗА ДЕНЬ
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        max_active_sessions=3,
        key_hash="key_hash",
        label="label"
    )

    assert api_key.current_status() == ApiKeyStatus.EXPIRED
    assert api_key.status == ApiKeyStatus.EXPIRED

    # Если апи ключ завершился ПРЯМ ЩАС
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc),
        max_active_sessions=3,
        key_hash="key_hash",
        label="label"
    )

    assert api_key.current_status() == ApiKeyStatus.EXPIRED
    assert api_key.status == ApiKeyStatus.EXPIRED


def test_current_status_when_status_revoked_but_revoked_at_is_none() -> None:
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=3,
        key_hash="key_hash",
        label="label",
        status=ApiKeyStatus.REVOKED
    )
    with pytest.raises(AssertionError):
        assert api_key.current_status() == ApiKeyStatus.REVOKED


def test_current_status_revoked_when_it_really_revoked() -> None:
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=3,
        key_hash="key_hash",
        label="label",
        status=ApiKeyStatus.REVOKED,
        revoked_at=datetime.now(timezone.utc) - timedelta(minutes=1)
    )

    assert api_key.current_status() == ApiKeyStatus.REVOKED


def test_current_status_if_not_revoked_and_not_expired() -> None:
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=3,
        key_hash="key_hash",
        label="label",
        revoked_at=datetime.now(timezone.utc) - timedelta(minutes=1)
    )

    assert api_key.status == ApiKeyStatus.ACTIVE