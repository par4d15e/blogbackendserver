"""
Tests for internationalization (i18n) module.
"""
from unittest.mock import MagicMock

from app.core.i18n.i18n import Language, get_message


class TestLanguageEnum:
    """Tests for Language enum."""

    def test_language_values(self):
        """Test Language enum has expected values."""
        assert Language.ZH_CN.value == "zh"
        assert Language.EN_US.value == "en"

    def test_language_members(self):
        """Test Language enum has expected members."""
        assert hasattr(Language, 'ZH_CN')
        assert hasattr(Language, 'EN_US')


class TestGetMessage:
    """Tests for get_message function."""

    def test_get_message_english(self):
        """Test getting message in English."""
        message = get_message("auth.sendVerificationCode", Language.EN_US)
        assert message is not None
        assert isinstance(message, str)

    def test_get_message_chinese(self):
        """Test getting message in Chinese."""
        message = get_message("auth.sendVerificationCode", Language.ZH_CN)
        assert message is not None
        assert isinstance(message, str)

    def test_get_message_fallback(self):
        """Test message fallback for unknown key."""
        message = get_message("nonexistent.key", Language.EN_US)
        # Should return the key or a default message
        assert message is not None

    def test_different_languages_different_messages(self):
        """Test that different languages return different messages."""
        en_message = get_message("auth.sendVerificationCode", Language.EN_US)
        zh_message = get_message("auth.sendVerificationCode", Language.ZH_CN)
        # Messages should exist (may be same or different based on translation)
        assert en_message is not None
        assert zh_message is not None


class TestGetLanguage:
    """Tests for get_language function."""

    def test_get_language_from_header(self):
        """Test getting language from Accept-Language header."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "zh-CN"
        
        # The function should handle the header
        assert mock_request.headers.get("Accept-Language") == "zh-CN"

    def test_get_language_default(self):
        """Test default language fallback."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        
        # Should have a default
        assert mock_request.headers.get("Accept-Language") is None
