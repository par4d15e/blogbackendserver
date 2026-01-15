"""
国际化支持模块
"""

import json
from pathlib import Path
from typing import Any, Optional
from enum import Enum
from contextvars import ContextVar
from functools import reduce
from fastapi import Request


class Language(Enum):
    """支持的语言枚举"""

    ZH_CN = "zh"
    EN_US = "en"


# 请求级别的语言上下文变量
_request_language: ContextVar[Language] = ContextVar(
    "request_language", default=Language.EN_US
)

# 消息文件目录
_MESSAGES_DIR = Path(__file__).parent / "messages"
_FALLBACK_MESSAGE = "Unknown error"


def _load_messages(language: Language) -> dict:
    """加载指定语言的消息文件"""
    try:
        file_path = _MESSAGES_DIR / f"{language.value}.json"
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load messages for {language.value}: {e}")
        return {}


def _get_nested(data: dict, keys: list[str]) -> Any:
    """安全获取嵌套字典值"""
    try:
        return reduce(lambda d, k: d[k], keys, data)
    except (KeyError, TypeError):
        return None


def _detect_language(header: Optional[str]) -> Optional[Language]:
    """从 header 值检测语言"""
    if not header:
        return None
    header_lower = header.lower()
    if header_lower.startswith("zh"):
        return Language.ZH_CN
    if header_lower.startswith("en"):
        return Language.EN_US
    return None


class I18nManager:
    """国际化管理器"""

    def __init__(self):
        self._messages = {lang: _load_messages(lang) for lang in Language}
        self._default_language = Language.EN_US

    def get_localized_message(
        self, key: str, language: Optional[Language] = None
    ) -> str:
        """获取指定语言的消息"""
        lang = language or self._default_language
        messages = self._messages.get(lang, self._messages[self._default_language])

        # 获取消息值
        keys = key.split(".") if key else []
        result = _get_nested(messages, keys) if keys else None

        # 如果结果是字符串则返回，否则返回 fallback
        if isinstance(result, str):
            return result

        # Fallback: common.internalError
        fallback = _get_nested(messages, ["common", "internalError"])
        return fallback if isinstance(fallback, str) else _FALLBACK_MESSAGE

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return [lang.value for lang in self._messages]


# 全局实例
i18n_manager = I18nManager()


def set_request_language(language: Language):
    """设置当前请求的语言"""
    _request_language.set(language)


def get_current_language() -> Language:
    """获取当前请求的语言"""
    return _request_language.get()


def get_language(request: Request) -> Language:
    """从请求解析语言，优先级: X-Language -> Accept-Language -> 默认英文"""
    # X-Language header
    if lang := _detect_language(request.headers.get("X-Language")):
        return lang

    # Accept-Language header
    accept = request.headers.get("Accept-Language") or ""
    for part in accept.split(","):
        tag = part.split(";")[0].strip()
        if lang := _detect_language(tag):
            return lang

    return Language.EN_US


def get_message(key: str, lang: Optional[Language] = None) -> str:
    """获取国际化消息"""
    return i18n_manager.get_localized_message(key, lang or get_current_language())
