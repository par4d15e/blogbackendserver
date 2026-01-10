"""
Tests for utility modules.
"""
import pytest
from datetime import datetime


class TestKeysetPagination:
    """Tests for keyset pagination utility."""

    def test_encode_cursor(self):
        """Test cursor encoding."""
        from app.utils.keyset_pagination import KeysetPaginator

        paginator = KeysetPaginator()
        cursor = paginator.encode_cursor(datetime(2024, 1, 1, 12, 0, 0), 123)
        assert cursor is not None
        assert isinstance(cursor, str)

    def test_decode_cursor_valid(self):
        """Test decoding a valid cursor."""
        from app.utils.keyset_pagination import KeysetPaginator

        paginator = KeysetPaginator()
        original_id = 456
        original_time = datetime(2024, 6, 15, 10, 30, 0)
        cursor = paginator.encode_cursor(original_time, original_id)

        decoded_time, decoded_id = paginator.decode_cursor(cursor)
        assert decoded_id == original_id
        assert decoded_time.year == original_time.year
        assert decoded_time.month == original_time.month
        assert decoded_time.day == original_time.day

    def test_decode_cursor_invalid(self):
        """Test decoding an invalid cursor."""
        from app.utils.keyset_pagination import KeysetPaginator

        paginator = KeysetPaginator()
        result = paginator.decode_cursor("invalid-cursor")
        assert result == (None, None)

    def test_decode_cursor_none(self):
        """Test decoding None cursor."""
        from app.utils.keyset_pagination import KeysetPaginator

        paginator = KeysetPaginator()
        result = paginator.decode_cursor(None)
        assert result == (None, None)


class TestAESJsonCipher:
    """Tests for AES encryption utility."""

    @pytest.fixture
    def cipher(self):
        """Create cipher with test key."""
        from app.utils.encrypt_data import AESJsonCipher
        # 32 bytes key for AES-256
        key = b"test-key-for-aes-32-bytes-long!!"[:32]
        return AESJsonCipher(key)

    def test_encrypt_decrypt_roundtrip(self, cipher):
        """Test encrypting and decrypting data."""
        original = {"key": "value", "number": 12345}
        encrypted = cipher.encrypt(original)
        decrypted = cipher.decrypt(encrypted)

        assert encrypted != str(original)
        assert decrypted == original

    def test_encrypt_produces_different_output(self, cipher):
        """Test that encryption produces different output each time (due to IV)."""
        data = {"test": "data"}
        encrypted1 = cipher.encrypt(data)
        encrypted2 = cipher.encrypt(data)

        # Should be different due to random IV
        assert encrypted1 != encrypted2

    def test_invalid_key_length(self):
        """Test that invalid key length raises error."""
        from app.utils.encrypt_data import AESJsonCipher

        with pytest.raises(ValueError, match="16, 24, or 32 bytes"):
            AESJsonCipher(b"short-key")


class TestSlugify:
    """Tests for slug generation."""

    def test_basic_slugify(self):
        """Test basic slug generation."""
        from slugify import slugify

        title = "Hello World"
        slug = slugify(title)
        assert slug == "hello-world"

    def test_slugify_special_chars(self):
        """Test slug generation with special characters."""
        from slugify import slugify

        title = "Hello! World? #123"
        slug = slugify(title)
        assert slug == "hello-world-123"

    def test_slugify_unicode(self):
        """Test slug generation with unicode."""
        from slugify import slugify

        title = "你好世界 Hello"
        slug = slugify(title)
        assert "hello" in slug


class TestEmailValidation:
    """Tests for email validation patterns."""

    def test_valid_email_pattern(self):
        """Test valid email patterns."""
        import re
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
        ]

        for email in valid_emails:
            assert re.match(pattern, email) is not None

    def test_invalid_email_pattern(self):
        """Test invalid email patterns."""
        import re
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        invalid_emails = [
            "invalid",
            "@nodomain.com",
            "no@domain",
            "spaces in@email.com",
        ]

        for email in invalid_emails:
            assert re.match(pattern, email) is None


class TestOffsetPagination:
    """Tests for offset pagination utility."""

    @pytest.fixture
    def paginator(self):
        """Create paginator instance."""
        from app.utils.offset_pagination import OffsetPaginator
        return OffsetPaginator(default_page_size=20, max_page_size=100)

    def test_validate_pagination_params_valid(self, paginator):
        """Test valid pagination params."""
        page, size = paginator.validate_pagination_params(1, 20)
        assert page == 1
        assert size == 20

    def test_validate_pagination_params_invalid_page(self, paginator):
        """Test invalid page raises error."""
        with pytest.raises(ValueError, match="Page number must be greater than 0"):
            paginator.validate_pagination_params(0, 20)

    def test_validate_pagination_params_max_size(self, paginator):
        """Test size is capped at max."""
        page, size = paginator.validate_pagination_params(1, 500)
        assert size == 100  # Max size

    def test_validate_pagination_params_default_size(self, paginator):
        """Test default size when invalid."""
        page, size = paginator.validate_pagination_params(1, 0)
        assert size == 20  # Default size


class TestClientInfo:
    """Tests for client info utility."""

    def test_client_info_utils_exists(self):
        """Test ClientInfoUtils class exists."""
        from app.utils.client_info import ClientInfoUtils
        utils = ClientInfoUtils()
        assert utils is not None

    def test_get_client_ip_from_headers_cf(self):
        """Test getting IP from Cloudflare header."""
        from app.utils.client_info import ClientInfoUtils
        utils = ClientInfoUtils()

        headers = {"CF-Connecting-IP": "1.2.3.4"}
        ip = utils.get_client_ip_from_headers(headers)
        assert ip == "1.2.3.4"

    def test_get_client_ip_from_headers_forwarded(self):
        """Test getting IP from X-Forwarded-For header."""
        from app.utils.client_info import ClientInfoUtils
        utils = ClientInfoUtils()

        headers = {"X-Forwarded-For": "5.6.7.8, 10.0.0.1"}
        ip = utils.get_client_ip_from_headers(headers)
        assert ip == "5.6.7.8"


class TestQRGenerator:
    """Tests for QR code generator."""

    def test_qr_generator_module_exists(self):
        """Test QR generator module exists."""
        from app.utils import qr_generator
        assert qr_generator is not None

    def test_generate_qr_code_function_exists(self):
        """Test generate_qr_code function exists."""
        from app.utils.qr_generator import generate_qr_code_from_encrypted_data
        assert callable(generate_qr_code_from_encrypted_data)


class TestLogger:
    """Tests for logger utility."""

    def test_logger_manager_exists(self):
        """Test LoggerManager class exists."""
        from app.core.logger import LoggerManager
        manager = LoggerManager()
        assert manager is not None

    def test_logger_manager_get_logger(self):
        """Test getting a logger instance."""
        from app.core.logger import logger_manager
        logger = logger_manager.get_logger(__name__)
        assert logger is not None


class TestCommonSchemas:
    """Tests for common schemas."""

    def test_success_response_schema(self):
        """Test SuccessResponse schema."""
        from app.schemas.common import SuccessResponse

        response = SuccessResponse(message="OK", data={"key": "value"})
        assert response.status == 200
        assert response.message == "OK"
        assert response.data == {"key": "value"}

    def test_notification_type_enum(self):
        """Test NotificationType enum."""
        from app.schemas.common import NotificationType

        assert NotificationType.FRIEND_REQUEST.value == "friend_request"
        assert NotificationType.PAYMENT_REQUEST.value == "payment_request"

    def test_large_content_translation_type_enum(self):
        """Test LargeContentTranslationType enum."""
        from app.schemas.common import LargeContentTranslationType

        assert LargeContentTranslationType.BLOG.value == "blog"
        assert LargeContentTranslationType.PROJECT.value == "project"


class TestIOUtils:
    """Tests for IO utilities."""

    def test_io_utils_module_exists(self):
        """Test io_utils module exists."""
        from app.utils import io_utils
        assert io_utils is not None


class TestS3Bucket:
    """Tests for S3 bucket utility."""

    def test_s3_bucket_module_exists(self):
        """Test s3_bucket module exists."""
        from app.utils import s3_bucket
        assert s3_bucket is not None

    def test_create_s3_bucket_function_exists(self):
        """Test create_s3_bucket function exists."""
        from app.utils.s3_bucket import create_s3_bucket
        assert callable(create_s3_bucket)


class TestCeleryApp:
    """Tests for Celery configuration."""

    def test_celery_app_exists(self):
        """Test celery app exists."""
        from app.core.celery import celery_app
        assert celery_app is not None

    def test_celery_app_name(self):
        """Test celery app has correct name."""
        from app.core.celery import celery_app
        assert celery_app.main is not None
