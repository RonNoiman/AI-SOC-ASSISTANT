import pytest
from datetime import datetime, timedelta
from auth.service import AuthService


def test_hash_and_verify_password():
    password = "SecurePass123!"
    hashed = AuthService.hash_password(password)
    assert hashed != password
    assert AuthService.verify_password(password, hashed)
    assert not AuthService.verify_password("wrong", hashed)


def test_validate_password_strength():
    assert AuthService.validate_password_strength("short") is not None
    assert AuthService.validate_password_strength("lowercase1!") is not None
    assert AuthService.validate_password_strength("UPPERCASE1!") is not None
    assert AuthService.validate_password_strength("NoNumber!") is not None
    assert AuthService.validate_password_strength("NoSpecial1") is not None
    assert AuthService.validate_password_strength("StrongPass1!") is None


def test_update_password():
    old_password = "OldPass123!"
    new_password = "NewPass456!"
    old_hash = AuthService.hash_password(old_password)

    class UserStub:
        hashed_password = old_hash

    class DBStub:
        def add(self, _obj):
            pass

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    user = UserStub()
    db = DBStub()

    AuthService.update_password(db, user, new_password)

    assert user.hashed_password != old_hash
    assert AuthService.verify_password(new_password, user.hashed_password)


def test_get_valid_password_reset_token_rejects_expired_or_used():
    class ResetTokenStub:
        def __init__(self, expires_at, used_at=None):
            self.expires_at = expires_at
            self.used_at = used_at

    class QueryStub:
        def __init__(self, token):
            self.token = token

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.token

    class DBStub:
        def __init__(self, token):
            self.token = token

        def query(self, _model):
            return QueryStub(self.token)

    valid_token = ResetTokenStub(datetime.utcnow() + timedelta(minutes=5))
    assert AuthService.get_valid_password_reset_token(DBStub(valid_token), "abc") is valid_token

    expired_token = ResetTokenStub(datetime.utcnow() - timedelta(minutes=1))
    assert AuthService.get_valid_password_reset_token(DBStub(expired_token), "abc") is None

    used_token = ResetTokenStub(datetime.utcnow() + timedelta(minutes=5), used_at=datetime.utcnow())
    assert AuthService.get_valid_password_reset_token(DBStub(used_token), "abc") is None


def test_register_failed_login_locks_after_threshold():
    class UserStub:
        failed_login_attempts = 4
        locked_until = None

    class DBStub:
        def add(self, _obj):
            pass

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    user = UserStub()
    updated_user, locked = AuthService.register_failed_login(DBStub(), user)

    assert updated_user.failed_login_attempts == 5
    assert locked is True
    assert updated_user.locked_until is not None


def test_reset_login_attempts_clears_lock():
    class UserStub:
        failed_login_attempts = 5
        locked_until = datetime.utcnow() + timedelta(minutes=15)

    class DBStub:
        def add(self, _obj):
            pass

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    user = UserStub()
    updated_user = AuthService.reset_login_attempts(DBStub(), user)

    assert updated_user.failed_login_attempts == 0
    assert updated_user.locked_until is None


def test_create_and_decode_token():
    token = AuthService.create_access_token({"sub": 1})
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "1"


def test_decode_invalid_token():
    assert AuthService.decode_token("invalid.token.here") is None
