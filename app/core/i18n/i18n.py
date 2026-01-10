"""
国际化支持模块
"""

import json
import os
from typing import Dict, Optional
from enum import Enum
from fastapi import Request


class Language(Enum):
    """支持的语言枚举"""

    ZH_CN = "zh"  # 简体中文
    EN_US = "en"  # 英文


class I18nManager:
    """国际化管理器"""

    def __init__(self):
        self._messages = {}
        self._default_language = Language.EN_US
        self._load_all_languages()

    def _load_all_languages(self):
        """加载所有支持的语言消息"""
        for language in Language:
            self._messages[language] = self._load_language_messages(language)

    def _load_language_messages(self, language: Language) -> Dict[str, str]:
        """从JSON文件加载指定语言的消息"""
        try:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            messages_dir = os.path.join(current_dir, "messages")
            file_path = os.path.join(messages_dir, f"{language.value}.json")

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 如果文件不存在或解析失败，返回空字典
            print(
                f"Warning: Failed to load messages for {language.value}: {e}")
            return {}

    def get_localized_message(self, key: str, language: Optional[Language] = None) -> str:
        """获取指定语言的消息"""
        if language is None:
            language = self._default_language

        messages = self._messages.get(
            language, self._messages[self._default_language])

        # 支持嵌套key访问，如 "common.internalError"
        if "." in key:
            keys = key.split(".")
            result = messages
            for k in keys:
                if isinstance(result, dict) and k in result:
                    result = result[k]
                else:
                    return messages.get("common", {}).get(
                        "internalError", "Unknown error"
                    )
            return (
                result
                if isinstance(result, str)
                else messages.get("common", {}).get("internalError", "Unknown error")
            )

        return messages.get(
            key, messages.get("common", {}).get(
                "internalError", "Unknown error")
        )

    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return [lang.value for lang in self._messages.keys()]


# 全局国际化管理器实例
i18n_manager = I18nManager()


def get_language(request: Request) -> Language:
    """Resolve request language with simplified fallbacks.

    Priority: X-Language header -> Accept-Language -> 'en'
    """
    # 1) Custom header (主要方式)
    lang = request.headers.get("X-Language")
    if lang and lang.startswith("zh"):
        return Language.ZH_CN
    if lang and lang.startswith("en"):
        return Language.EN_US

    # 2) Accept-Language (浏览器默认语言)
    accept_language = request.headers.get("Accept-Language")
    if not accept_language:
        return Language.EN_US
    for part in accept_language.split(","):
        tag = part.split(";")[0].strip().lower()
        if tag.startswith("zh"):
            return Language.ZH_CN
        if tag.startswith("en"):
            return Language.EN_US
    return Language.EN_US


def get_message(key: str, lang: Language) -> str:
    """获取错误消息的便捷函数"""
    return i18n_manager.get_localized_message(key, lang)
