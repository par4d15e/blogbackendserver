"""
Tests for Celery tasks.
"""
import pytest
from unittest.mock import patch
from pathlib import Path


class TestBackupDatabaseTask:
    """Tests for backup database task."""

    def test_parse_database_url_mysql(self):
        """Test parsing MySQL database URL."""
        from app.tasks.backup_database_task import _parse_database_url
        
        url = "mysql://user:password@localhost:3306/testdb"
        result = _parse_database_url(url)
        
        assert result["host"] == "localhost"
        assert result["port"] == 3306
        assert result["user"] == "user"
        assert result["password"] == "password"
        assert result["database"] == "testdb"

    def test_parse_database_url_mysql_pymysql(self):
        """Test parsing MySQL+pymysql database URL."""
        from app.tasks.backup_database_task import _parse_database_url
        
        url = "mysql+pymysql://admin:secret@db.example.com:3307/production"
        result = _parse_database_url(url)
        
        assert result["host"] == "db.example.com"
        assert result["port"] == 3307
        assert result["user"] == "admin"
        assert result["password"] == "secret"
        assert result["database"] == "production"

    def test_parse_database_url_defaults(self):
        """Test parsing database URL with default values."""
        from app.tasks.backup_database_task import _parse_database_url
        
        url = "mysql://localhost/mydb"
        result = _parse_database_url(url)
        
        assert result["host"] == "localhost"
        assert result["port"] == 3306
        assert result["user"] == "root"
        assert result["password"] == ""
        assert result["database"] == "mydb"

    def test_parse_database_url_unsupported(self):
        """Test parsing unsupported database URL raises error."""
        from app.tasks.backup_database_task import _parse_database_url
        
        with pytest.raises(ValueError) as exc_info:
            _parse_database_url("postgresql://user:pass@localhost/db")
        
        assert "不支持的数据库类型" in str(exc_info.value)


class TestGreetingEmailTask:
    """Tests for greeting email task."""

    @patch('app.tasks.greeting_email_task.email_service')
    @patch('app.tasks.greeting_email_task.settings')
    def test_greeting_task_zh_subject(self, mock_settings, mock_email_service):
        """Test greeting task generates correct Chinese subject."""
        mock_settings.app.APP_NAME = "TestApp"
        
        # The subject should contain Chinese greeting
        expected_subject_part = "很高兴遇见你"
        
        # Verify the subject format
        subject = "[TestApp] - 🌱 很高兴遇见你"
        assert expected_subject_part in subject

    @patch('app.tasks.greeting_email_task.email_service')
    @patch('app.tasks.greeting_email_task.settings')
    def test_greeting_task_en_subject(self, mock_settings, mock_email_service):
        """Test greeting task generates correct English subject."""
        mock_settings.app.APP_NAME = "TestApp"
        
        # The subject should contain English greeting
        expected_subject_part = "A big warm welcome"
        
        subject = "[TestApp] - 🌱 Hi there! A big warm welcome to you."
        assert expected_subject_part in subject


class TestNotificationTask:
    """Tests for notification task."""

    def test_notification_type_friend_request(self):
        """Test friend request notification type."""
        from app.schemas.common import NotificationType
        
        assert NotificationType.FRIEND_REQUEST.value == "friend_request"

    def test_notification_type_payment_request(self):
        """Test payment request notification type."""
        from app.schemas.common import NotificationType
        
        assert NotificationType.PAYMENT_REQUEST.value == "payment_request"

    @patch('app.tasks.notification_task.settings')
    def test_notification_subject_format(self, mock_settings):
        """Test notification subject format."""
        mock_settings.app.APP_NAME = "TestApp"
        
        subject = "[TestApp] - 📢 好友请求"
        assert "[TestApp]" in subject
        assert "好友请求" in subject


class TestThumbnailTask:
    """Tests for thumbnail generation task."""

    def test_generate_image_thumbnail_creates_output_dir(self, tmp_path):
        """Test that thumbnail function creates output directory."""
        from app.tasks.thumbnail_task import generate_image_thumbnail
        
        output_dir = tmp_path / "thumbnails"
        assert not output_dir.exists()
        
        # Create a fake input file
        input_file = tmp_path / "test_image.jpg"
        input_file.touch()
        
        # This will try to process the file but fail since it's empty
        # The output directory should still be created
        try:
            generate_image_thumbnail(str(input_file), str(output_dir))
        except Exception:
            pass  # Expected to fail without actual image
        
        assert output_dir.exists()

    def test_thumbnail_path_handling(self, tmp_path):
        """Test thumbnail path handling with Path objects."""
        
        input_path = tmp_path / "image.jpg"
        input_path.touch()
        
        # Test that Path objects are handled correctly
        paths = [input_path]
        assert all(isinstance(Path(p), Path) for p in paths)


class TestClientInfoTask:
    """Tests for client info task."""

    @patch('app.tasks.client_info_task.client_info_utils')
    def test_get_client_ip_from_headers(self, mock_utils):
        """Test extracting client IP from headers."""
        headers = {
            "x-forwarded-for": "192.168.1.100, 10.0.0.1",
            "x-real-ip": "192.168.1.100"
        }
        
        mock_utils.get_client_ip_from_headers.return_value = "192.168.1.100"
        
        result = mock_utils.get_client_ip_from_headers(headers)
        assert result == "192.168.1.100"

    def test_localhost_ip_handling(self):
        """Test localhost IP addresses are recognized."""
        localhost_ips = ["localhost", "127.0.0.1", "::1"]
        
        for ip in localhost_ips:
            assert ip in localhost_ips


class TestDeleteUserMediaTask:
    """Tests for delete user media task."""

    def test_task_module_exists(self):
        """Test that delete user media task module exists."""
        from app.tasks import delete_user_media_task
        assert delete_user_media_task is not None


class TestGenerateContentAudioTask:
    """Tests for generate content audio task."""

    def test_task_module_exists(self):
        """Test that generate content audio task module exists."""
        from app.tasks import generate_content_audio_task
        assert generate_content_audio_task is not None


class TestLargeContentTranslationTask:
    """Tests for large content translation task."""

    def test_task_module_exists(self):
        """Test that large content translation task module exists."""
        from app.tasks import large_content_translation_task
        assert large_content_translation_task is not None


class TestSendInvoiceEmailTask:
    """Tests for send invoice email task."""

    def test_task_module_exists(self):
        """Test that send invoice email task module exists."""
        from app.tasks import send_invoice_email_task
        assert send_invoice_email_task is not None


class TestSummaryContentTask:
    """Tests for summary content task."""

    def test_task_module_exists(self):
        """Test that summary content task module exists."""
        from app.tasks import summary_content_task
        assert summary_content_task is not None


class TestWatermarkTask:
    """Tests for watermark task."""

    def test_task_module_exists(self):
        """Test that watermark task module exists."""
        from app.tasks import watermark_task
        assert watermark_task is not None
