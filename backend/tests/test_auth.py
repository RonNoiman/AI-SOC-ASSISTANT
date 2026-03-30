import pytest
from auth.service import AuthService


def test_hash_and_verify_password():
    password = "SecurePass123!"
    hashed = AuthService.hash_password(password)
    assert hashed != password
    assert AuthService.verify_password(password, hashed)
    assert not AuthService.verify_password("wrong", hashed)


def test_create_and_decode_token():
    token = AuthService.create_access_token({"sub": 1})
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "1"


def test_decode_invalid_token():
    assert AuthService.decode_token("invalid.token.here") is None
