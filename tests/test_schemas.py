"""
Tests for Pydantic schemas validation.
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth_schemas import (
    EmailSchema,
    CodeSchema,
    PasswordSchema,
    UsernameSchema,
    SendCodeRequest,
    CreateUserAccountRequest,
    ResetPasswordRequest,
    AccountLoginRequest,
)
from app.schemas.user_schemas import BioRequest, EnableDisableUserRequest


class TestAuthSchemas:
    """Tests for authentication schemas."""

    def test_email_schema_valid(self):
        """Test valid email schema."""
        schema = EmailSchema(email="test@example.com")
        assert schema.email == "test@example.com"

    def test_email_schema_default(self):
        """Test email schema default value."""
        schema = EmailSchema()
        assert schema.email == "ln729500172@gmail.com"

    def test_code_schema_valid(self):
        """Test valid code schema."""
        schema = CodeSchema(code="123456")
        assert schema.code == "123456"

    def test_password_schema_valid(self):
        """Test valid password schema."""
        schema = PasswordSchema(password="SecurePass123!")
        assert schema.password == "SecurePass123!"

    def test_username_schema_valid(self):
        """Test valid username schema."""
        schema = UsernameSchema(username="testuser123")
        assert schema.username == "testuser123"

    def test_send_code_request(self):
        """Test SendCodeRequest schema."""
        request = SendCodeRequest(email="user@example.com")
        assert request.email == "user@example.com"

    def test_create_user_account_request_valid(self):
        """Test valid CreateUserAccountRequest."""
        request = CreateUserAccountRequest(
            email="new@example.com",
            code="654321",
            password="StrongPass1!",
            username="newuser",
        )
        assert request.email == "new@example.com"
        assert request.code == "654321"
        assert request.password == "StrongPass1!"
        assert request.username == "newuser"

    def test_reset_password_request_valid(self):
        """Test valid ResetPasswordRequest."""
        request = ResetPasswordRequest(
            email="reset@example.com",
            code="111222",
            password="NewPass123!",
        )
        assert request.email == "reset@example.com"
        assert request.code == "111222"
        assert request.password == "NewPass123!"

    def test_account_login_request_valid(self):
        """Test valid AccountLoginRequest."""
        request = AccountLoginRequest(
            email="login@example.com",
            password="LoginPass1!",
        )
        assert request.email == "login@example.com"
        assert request.password == "LoginPass1!"


class TestUserSchemas:
    """Tests for user schemas."""

    def test_bio_request_valid(self):
        """Test valid BioRequest."""
        request = BioRequest(bio="This is my bio")
        assert request.bio == "This is my bio"

    def test_bio_request_min_length(self):
        """Test BioRequest minimum length validation."""
        with pytest.raises(ValidationError):
            BioRequest(bio="")

    def test_bio_request_max_length(self):
        """Test BioRequest maximum length validation."""
        with pytest.raises(ValidationError):
            BioRequest(bio="x" * 256)

    def test_enable_disable_user_request(self):
        """Test EnableDisableUserRequest."""
        request = EnableDisableUserRequest(user_id=1, is_active=True)
        assert request.user_id == 1
        assert request.is_active is True

    def test_enable_disable_user_request_default(self):
        """Test EnableDisableUserRequest default values."""
        request = EnableDisableUserRequest(user_id=2)
        assert request.user_id == 2
        assert request.is_active is False
