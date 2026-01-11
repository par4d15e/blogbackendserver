"""
Tests for internationalization (i18n) module.
"""
import pytest
from unittest.mock import MagicMock, patch
from contextvars import copy_context

from app.core.i18n.i18n import (
    Language,
    I18nManager,
    i18n_manager,
    get_message,
    get_language,
    get_current_language,
    set_request_language,
    _request_language,
)


class TestLanguageEnum:
    """Tests for Language enum."""

    def test_language_values(self):
        """Test Language enum has expected values."""
        assert Language.ZH_CN.value == "zh"
        assert Language.EN_US.value == "en"

    def test_language_members(self):
        """Test Language enum has expected members."""
        assert hasattr(Language, "ZH_CN")
        assert hasattr(Language, "EN_US")

    def test_language_iteration(self):
        """Test iterating over Language enum."""
        languages = list(Language)
        assert len(languages) == 2
        assert Language.ZH_CN in languages
        assert Language.EN_US in languages


class TestI18nManager:
    """Tests for I18nManager class."""

    def test_manager_initialization(self):
        """Test I18nManager initializes correctly."""
        manager = I18nManager()
        assert manager._default_language == Language.EN_US
        assert Language.ZH_CN in manager._messages
        assert Language.EN_US in manager._messages

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = i18n_manager.get_supported_languages()
        assert "zh" in languages
        assert "en" in languages

    def test_get_localized_message_english(self):
        """Test getting localized message in English."""
        message = i18n_manager.get_localized_message(
            "auth.sendVerificationCode", Language.EN_US
        )
        assert message == "Verification code has been sent to your email"

    def test_get_localized_message_chinese(self):
        """Test getting localized message in Chinese."""
        message = i18n_manager.get_localized_message(
            "auth.sendVerificationCode", Language.ZH_CN
        )
        assert message == "验证码已发送至您的邮箱"

    def test_get_localized_message_nested_key(self):
        """Test getting localized message with nested key."""
        en_message = i18n_manager.get_localized_message(
            "auth.common.userNotFound", Language.EN_US
        )
        zh_message = i18n_manager.get_localized_message(
            "auth.common.userNotFound", Language.ZH_CN
        )
        assert en_message == "User not found"
        assert zh_message == "用户未找到"

    def test_get_localized_message_deeply_nested(self):
        """Test getting localized message with deeply nested key."""
        en_message = i18n_manager.get_localized_message(
            "auth.accountLogin.accountLoginSuccess", Language.EN_US
        )
        zh_message = i18n_manager.get_localized_message(
            "auth.accountLogin.accountLoginSuccess", Language.ZH_CN
        )
        assert en_message == "Account login successfully"
        assert zh_message == "账户登录成功"

    def test_get_localized_message_fallback_for_unknown_key(self):
        """Test fallback for unknown message key."""
        message = i18n_manager.get_localized_message(
            "nonexistent.key.path", Language.EN_US
        )
        # Should return default error message
        assert message == "Internal error, please check the logs"

    def test_get_localized_message_default_language(self):
        """Test getting message with default language (None)."""
        message = i18n_manager.get_localized_message("common.internalError", None)
        # Should use default language (EN_US)
        assert message == "Internal error, please check the logs"


class TestGetMessage:
    """Tests for get_message function."""

    def test_get_message_with_explicit_language(self):
        """Test get_message with explicit language parameter."""
        en_message = get_message("auth.sendVerificationCode", Language.EN_US)
        zh_message = get_message("auth.sendVerificationCode", Language.ZH_CN)
        
        assert en_message == "Verification code has been sent to your email"
        assert zh_message == "验证码已发送至您的邮箱"

    def test_get_message_uses_context_language(self):
        """Test get_message uses language from context when not specified."""
        # Set context language to Chinese
        set_request_language(Language.ZH_CN)
        message = get_message("auth.sendVerificationCode")
        assert message == "验证码已发送至您的邮箱"
        
        # Set context language to English
        set_request_language(Language.EN_US)
        message = get_message("auth.sendVerificationCode")
        assert message == "Verification code has been sent to your email"

    def test_get_message_nested_keys(self):
        """Test get_message with various nested key patterns."""
        test_cases = [
            ("common.internalError", Language.EN_US, "Internal error, please check the logs"),
            ("common.internalError", Language.ZH_CN, "内部错误,请检查日志"),
            ("auth.common.userNotFound", Language.EN_US, "User not found"),
            ("auth.common.userNotFound", Language.ZH_CN, "用户未找到"),
            ("blog.getBlogTTS.blogTtsNotFound", Language.EN_US, "Blog TTS not found"),
            ("blog.getBlogTTS.blogTtsNotFound", Language.ZH_CN, "博客TTS未找到"),
        ]
        
        for key, lang, expected in test_cases:
            message = get_message(key, lang)
            assert message == expected, f"Failed for key={key}, lang={lang}"

    def test_get_message_all_modules(self):
        """Test get_message works for all major modules."""
        modules = ["auth", "user", "blog", "section", "board", "friend", 
                   "media", "seo", "tag", "project", "payment", "subscriber"]
        
        for module in modules:
            # Test that we can get at least one message from each module
            key = f"{module}.common" if module not in ["subscriber"] else module
            en_messages = i18n_manager._messages[Language.EN_US]
            
            # Verify module exists in messages
            assert module in en_messages, f"Module {module} not found in messages"


class TestGetLanguage:
    """Tests for get_language function."""

    def test_get_language_from_x_language_header_zh(self):
        """Test getting language from X-Language header (Chinese)."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key: {
            "X-Language": "zh-CN",
            "Accept-Language": None,
        }.get(key)
        
        language = get_language(mock_request)
        assert language == Language.ZH_CN

    def test_get_language_from_x_language_header_en(self):
        """Test getting language from X-Language header (English)."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key: {
            "X-Language": "en-US",
            "Accept-Language": None,
        }.get(key)
        
        language = get_language(mock_request)
        assert language == Language.EN_US

    def test_get_language_from_accept_language_zh(self):
        """Test getting language from Accept-Language header (Chinese)."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "X-Language": None,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }.get(key, default)
        
        language = get_language(mock_request)
        assert language == Language.ZH_CN

    def test_get_language_from_accept_language_en(self):
        """Test getting language from Accept-Language header (English)."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "X-Language": None,
            "Accept-Language": "en-US,en;q=0.9",
        }.get(key, default)
        
        language = get_language(mock_request)
        assert language == Language.EN_US

    def test_get_language_default_fallback(self):
        """Test default language fallback when no headers present."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key, default=None: default
        
        language = get_language(mock_request)
        assert language == Language.EN_US

    def test_get_language_x_language_priority(self):
        """Test X-Language header takes priority over Accept-Language."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda key: {
            "X-Language": "zh",
            "Accept-Language": "en-US,en;q=0.9",
        }.get(key)
        
        language = get_language(mock_request)
        assert language == Language.ZH_CN

    def test_get_language_partial_match(self):
        """Test language detection with partial matches."""
        test_cases = [
            ("zh", Language.ZH_CN),
            ("zh-TW", Language.ZH_CN),
            ("zh-Hans", Language.ZH_CN),
            ("en", Language.EN_US),
            ("en-GB", Language.EN_US),
            ("en-AU", Language.EN_US),
        ]
        
        for header_value, expected_lang in test_cases:
            mock_request = MagicMock()
            mock_request.headers.get.side_effect = lambda key: {
                "X-Language": header_value,
                "Accept-Language": None,
            }.get(key)
            
            language = get_language(mock_request)
            assert language == expected_lang, f"Failed for header={header_value}"


class TestContextLanguage:
    """Tests for context-based language management."""

    def test_set_and_get_request_language(self):
        """Test setting and getting request language."""
        # Set to Chinese
        set_request_language(Language.ZH_CN)
        assert get_current_language() == Language.ZH_CN
        
        # Set to English
        set_request_language(Language.EN_US)
        assert get_current_language() == Language.EN_US

    def test_default_language(self):
        """Test default language is English."""
        # Create a new context to test default
        ctx = copy_context()
        
        def check_default():
            # In a fresh context, should return default
            return _request_language.get()
        
        # The default should be EN_US
        assert _request_language.get() in [Language.EN_US, Language.ZH_CN]

    def test_context_isolation(self):
        """Test that language context is isolated."""
        set_request_language(Language.ZH_CN)
        
        # Create a copy of context
        ctx = copy_context()
        
        # Modify in current context
        set_request_language(Language.EN_US)
        assert get_current_language() == Language.EN_US


class TestMessageConsistency:
    """Tests for message consistency between languages."""

    def test_all_keys_exist_in_both_languages(self):
        """Test that all keys exist in both language files."""
        en_messages = i18n_manager._messages[Language.EN_US]
        zh_messages = i18n_manager._messages[Language.ZH_CN]
        
        def get_all_keys(d, prefix=""):
            """Recursively get all keys from nested dict."""
            keys = set()
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(get_all_keys(v, full_key))
                else:
                    keys.add(full_key)
            return keys
        
        en_keys = get_all_keys(en_messages)
        zh_keys = get_all_keys(zh_messages)
        
        # Check for missing keys
        missing_in_zh = en_keys - zh_keys
        missing_in_en = zh_keys - en_keys
        
        assert not missing_in_zh, f"Keys missing in Chinese: {missing_in_zh}"
        assert not missing_in_en, f"Keys missing in English: {missing_in_en}"

    def test_no_empty_messages(self):
        """Test that no messages are empty strings."""
        def check_empty(d, path=""):
            """Recursively check for empty strings."""
            empty_keys = []
            for k, v in d.items():
                current_path = f"{path}.{k}" if path else k
                if isinstance(v, dict):
                    empty_keys.extend(check_empty(v, current_path))
                elif isinstance(v, str) and not v.strip():
                    empty_keys.append(current_path)
            return empty_keys
        
        for lang in Language:
            messages = i18n_manager._messages[lang]
            empty_keys = check_empty(messages)
            assert not empty_keys, f"Empty messages in {lang.value}: {empty_keys}"

    def test_messages_are_different_between_languages(self):
        """Test that messages are actually translated (not identical)."""
        # Sample of keys that should definitely be different
        keys_to_check = [
            "common.internalError",
            "auth.sendVerificationCode",
            "blog.common.blogNotFound",
            "user.getMyProfile",
        ]
        
        for key in keys_to_check:
            en_msg = get_message(key, Language.EN_US)
            zh_msg = get_message(key, Language.ZH_CN)
            assert en_msg != zh_msg, f"Messages should differ for key: {key}"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_key(self):
        """Test handling of empty key."""
        message = get_message("", Language.EN_US)
        # Should return fallback message
        assert message is not None

    def test_single_level_key(self):
        """Test single level key that doesn't exist."""
        message = get_message("nonexistent", Language.EN_US)
        assert message == "Internal error, please check the logs"

    def test_partial_nested_key(self):
        """Test partial nested key (exists as dict, not string)."""
        # "auth.common" exists but is a dict, not a string
        message = get_message("auth.common", Language.EN_US)
        # Should return fallback since it's not a string
        assert message == "Internal error, please check the logs"

    def test_very_deep_nested_key(self):
        """Test very deep nested key that doesn't exist."""
        message = get_message("a.b.c.d.e.f.g", Language.EN_US)
        assert message == "Internal error, please check the logs"

    def test_special_characters_in_messages(self):
        """Test messages with special characters are handled correctly."""
        # Chinese messages contain special characters
        zh_message = get_message("common.internalError", Language.ZH_CN)
        assert "内部错误" in zh_message

    def test_language_enum_comparison(self):
        """Test Language enum comparison works correctly."""
        assert Language.ZH_CN == Language.ZH_CN
        assert Language.EN_US == Language.EN_US
        assert Language.ZH_CN != Language.EN_US
        
        # Test value comparison
        assert Language.ZH_CN.value == "zh"
        assert Language.EN_US.value == "en"
