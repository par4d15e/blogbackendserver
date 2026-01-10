"""
Tests for security module - password validation, hashing, and JWT.
"""
import pytest
from datetime import datetime

from app.core.security import (
    PasswordValidator,
    PasswordHasher,
    JWTManager,
    SecurityManager,
)


class TestPasswordValidator:
    """Tests for PasswordValidator class."""

    @pytest.fixture
    def validator(self):
        return PasswordValidator(min_length=8)

    def test_valid_password(self, validator):
        """Test password that meets all requirements."""
        assert validator.validate("SecurePass1!") is True

    def test_password_too_short(self, validator):
        """Test password that is too short."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validator.validate("Short1!")

    def test_password_no_uppercase(self, validator):
        """Test password without uppercase letter."""
        with pytest.raises(ValueError, match="uppercase letter"):
            validator.validate("securepass1!")

    def test_password_no_lowercase(self, validator):
        """Test password without lowercase letter."""
        with pytest.raises(ValueError, match="lowercase letter"):
            validator.validate("SECUREPASS1!")

    def test_password_no_digit(self, validator):
        """Test password without digit."""
        with pytest.raises(ValueError, match="one digit"):
            validator.validate("SecurePass!")

    def test_password_no_special_char(self, validator):
        """Test password without special character."""
        with pytest.raises(ValueError, match="special character"):
            validator.validate("SecurePass1")

    def test_custom_min_length(self):
        """Test custom minimum length."""
        validator = PasswordValidator(min_length=12)
        with pytest.raises(ValueError, match="at least 12 characters"):
            validator.validate("Short1!")


class TestPasswordHasher:
    """Tests for PasswordHasher class."""

    @pytest.fixture
    def hasher(self):
        return PasswordHasher()

    def test_hash_password(self, hasher):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hasher.hash(password)
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$argon2")

    def test_verify_password_correct(self, hasher):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hasher.hash(password)
        assert hasher.verify(password, hashed) is True

    def test_verify_password_incorrect(self, hasher):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hasher.hash(password)
        assert hasher.verify(wrong_password, hashed) is False

    def test_hash_uniqueness(self, hasher):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)
        assert hash1 != hash2  # Due to random salt


class TestJWTManager:
    """Tests for JWTManager class."""

    @pytest.fixture
    def jwt_manager(self):
        return JWTManager(
            secret_key="test-secret-key-for-testing-only",
            algorithm="HS256",
            issuer="test-issuer",
            audience="test-audience",
            access_token_expiry=3600,
            refresh_token_expiry=86400,
        )

    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        user_data = {"user_id": 123}
        token, exp_time = jwt_manager.create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert isinstance(exp_time, datetime)

    def test_create_refresh_token(self, jwt_manager):
        """Test refresh token creation."""
        user_data = {"user_id": 123}
        token, exp_time = jwt_manager.create_refresh_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert isinstance(exp_time, datetime)

    def test_decode_valid_token(self, jwt_manager):
        """Test decoding a valid token."""
        user_data = {"user_id": 456}
        token, _ = jwt_manager.create_access_token(user_data)
        payload = jwt_manager.decode_token(token)
        assert payload is not None
        assert payload.get("user_id") == 456

    def test_decode_invalid_token(self, jwt_manager):
        """Test decoding an invalid token."""
        payload = jwt_manager.decode_token("invalid.token.here")
        assert payload is None

    def test_token_contains_user_id(self, jwt_manager):
        """Test that token payload contains user_id."""
        user_data = {"user_id": 999}
        token, _ = jwt_manager.create_access_token(user_data)
        payload = jwt_manager.decode_token(token)
        assert payload["user_id"] == 999


class TestSecurityManager:
    """Tests for SecurityManager class."""

    @pytest.fixture
    def security_manager(self):
        from app.core.config.settings import settings
        return SecurityManager(settings)

    def test_security_manager_has_components(self, security_manager):
        """Test that SecurityManager has all components."""
        assert hasattr(security_manager, 'validator')
        assert hasattr(security_manager, 'hasher')
        assert hasattr(security_manager, 'jwt_manager')

    def test_validate_and_hash_password(self, security_manager):
        """Test validating and hashing password."""
        password = "ValidPass123!"
        security_manager.validator.validate(password)
        hashed = security_manager.hasher.hash(password)
        assert hashed is not None
        assert security_manager.hasher.verify(password, hashed)

    def test_create_and_verify_tokens(self, security_manager):
        """Test creating and verifying tokens."""
        user_data = {"user_id": 100}
        access_token, _ = security_manager.jwt_manager.create_access_token(user_data)
        refresh_token, _ = security_manager.jwt_manager.create_refresh_token(user_data)
        
        access_payload = security_manager.jwt_manager.decode_token(access_token)
        refresh_payload = security_manager.jwt_manager.decode_token(refresh_token)
        
        assert access_payload["user_id"] == 100
        assert refresh_payload["user_id"] == 100
