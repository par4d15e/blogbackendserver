import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Literal
from fastapi import HTTPException
from dashscope import Generation
import azure.cognitiveservices.speech as speechsdk
from app.core.logger import logger_manager

from app.core.config.settings import settings

Language = Literal["zh", "en"]


class AgentUtils:
    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)
        self.api_key = settings.qwen.QWEN_API_KEY.get_secret_value()
        self.tts_api_key = settings.azure.AZURE_SPEECH_KEY.get_secret_value()
        self.tts_region = settings.azure.AZURE_SPEECH_REGION

        self.translation_model = "qwen-max"
        self.translation_max_tokens = 2000
        self.translation_temperature = 0.1
        self.translation_top_p = 0.8
        self.translation_timeout = 30
        self.max_retries = 3

    @staticmethod
    def _normalize_english_spacing(text: str) -> str:
        """
        标准化英文文本的空格，确保单词间只有一个标准空格
        处理各种空白字符（空格、制表符、不间断空格等）

        Args:
            text: 需要标准化的文本

        Returns:
            标准化后的文本，所有空格都是标准的单个空格
        """
        if not text or not isinstance(text, str):
            return text

        # 1. 将所有类型的空白字符（空格、制表符、不间断空格等）统一替换为标准空格
        # \s 匹配所有空白字符，包括空格、制表符、换行符等
        # 但保留换行符，只处理水平空白
        text = re.sub(
            r'[\t\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]+', ' ', text)

        # 2. 将多个连续的标准空格替换为单个空格
        text = re.sub(r' {2,}', ' ', text)

        # 3. 确保标点符号前没有空格，后面有空格（除了句末）
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])(?!\s|$)', r'\1 ', text)

        # 4. 移除行首行尾的空格
        text = text.strip()

        return text

    # 严格检查是否包含中文
    def _contains_chinese_strict(self, text: str) -> bool:
        for ch in text:
            cp = ord(ch)
            # 中文字符范围
            if (
                0x4E00 <= cp <= 0x9FFF
                or 0x3400 <= cp <= 0x4DBF
                or 0x20000 <= cp <= 0x2A6DF
                or 0x2A700 <= cp <= 0x2B73F
                or 0x2B740 <= cp <= 0x2B81F
                or 0x2B820 <= cp <= 0x2CEAF
                or 0x2CEB0 <= cp <= 0x2EBEF
            ):
                return True
            # 中文标点符号范围
            if (
                0x3000 <= cp <= 0x303F  # CJK符号和标点
                or 0xFF00 <= cp <= 0xFFEF  # 全角ASCII、半角片假名、全角符号
            ):
                return True
        return False

    def synthesize(
        self,
        text: str,
        language: Language = "zh",
    ) -> Dict[str, str]:
        try:
            # 配置 Azure Speech SDK
            speech_config = speechsdk.SpeechConfig(
                subscription=self.tts_api_key,
                region=self.tts_region
            )

            # 根据语言设置语音
            voice_name = "zh-CN-XiaoxiaoNeural" if language == "zh" else "en-US-AvaMultilingualNeural"
            speech_config.speech_synthesis_voice_name = voice_name

            # 设置输出格式为 MP3
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
            )

            # 创建语音合成器（不需要音频输出配置，直接获取音频数据）
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config
            )

            # 执行语音合成
            result = synthesizer.speak_text_async(text).get()

            # 检查合成结果
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # 获取音频数据
                audio_data = result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                raise Exception(
                    f"Speech synthesis canceled: {cancellation_details.reason}")
            else:
                raise Exception(
                    f"Speech synthesis failed with reason: {result.reason}")

        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"TTS request failed: {exc}")

        # 处理音频数据
        try:
            # 将音频数据写入临时文件
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_temp:
                mp3_temp.write(audio_data)
                mp3_path = mp3_temp.name
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Failed to save audio data: {exc}")

        # ====== 使用 FFmpeg 直接转换 MP3 到 Opus ======
        try:
            # 1. MP3文件已经创建好了，使用现有的 mp3_path
            # 2. 创建Opus临时文件路径（注意：NamedTemporaryFile在Windows上无法二次打开）
            opus_path = tempfile.mktemp(suffix=".opus")

            # 3. 调用FFmpeg进行转换
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # 自动覆盖输出文件
                "-i",
                mp3_path,
                "-c:a",
                "libopus",  # 使用Opus编码器
                "-b:a",
                "64k",  # 64kbps比特率（语音优化）
                "-application",
                "voip",  # 语音优化模式
                "-frame_duration",
                "20",  # 帧时长（20ms是WebRTC标准）
                opus_path,
            ]

            # 执行FFmpeg命令
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 转换超时时间
            )

            # 4. 检查转换是否成功
            if result.returncode != 0:
                error_msg = (
                    result.stderr.strip()
                    or "FFmpeg conversion failed with unknown error"
                )
                raise RuntimeError(f"FFmpeg conversion failed: {error_msg}")

            # 5. 验证输出文件是否存在且非空
            if not Path(opus_path).exists() or Path(opus_path).stat().st_size == 0:
                raise RuntimeError(
                    "Conversion succeeded but output file is empty or missing"
                )

            # 6. 清理临时MP3文件
            Path(mp3_path).unlink(missing_ok=True)

            # 7. 返回Opus文件路径， 使用后需要删除
            return {"audio_path": opus_path}

        except Exception as exc:
            # 资源清理
            if "mp3_path" in locals():
                try:
                    Path(mp3_path).unlink(missing_ok=True)
                except:
                    pass
            if "opus_path" in locals() and Path(opus_path).exists():
                try:
                    Path(opus_path).unlink(missing_ok=True)
                except:
                    pass

            raise HTTPException(
                status_code=400, detail=f"Audio conversion failed: {str(exc)}"
            )

    async def translate(self, text: str) -> str:
        """
        使用Qwen API翻译文本

        Args:
            text: 要翻译的文本
            lang: 目标语言，"zh"表示中文，"en"表示英文

        Returns:
            翻译后的文本

        Raises:
            HTTPException: 翻译失败时抛出
        """
        if not text or not text.strip():
            raise HTTPException(status_code=404, detail="Text not found")

        if not self._contains_chinese_strict(text):
            raise HTTPException(
                status_code=404, detail="No Chinese text found")

        try:
            # 构建优化的翻译提示词 使用中文翻译成英文
            system_prompt = """
            You are a professional translator assistant specializing in accurate and natural English translations.
            Follow these requirements strictly:
            1. Carefully analyze the Chinese source text to understand its full meaning, context, and tone
            2. Translate the text into English while:
            - Maintaining the original meaning and intent
            - Using natural, fluent English expressions
            - Preserving the original tone (formal, casual, technical, etc.)
            - Keeping any specialized terminology accurate
            - Maintaining paragraph structure and formatting
            - For blog content, ensure the translation sounds engaging and natural to native English speakers
            3. If there are cultural references or idioms, translate them into appropriate English equivalents
            4. Output ONLY the translated text without explanations, notes, or source text
            5. Ensure the translated text follows English grammar rules and expression patterns
            """

            # 调用Qwen API进行翻译
            response = Generation.call(
                model=self.translation_model,
                api_key=self.api_key,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=self.translation_max_tokens,
                temperature=self.translation_temperature,
                top_p=self.translation_top_p,
                result_format="message",
            )

            # 检查API响应状态
            if not hasattr(response, "status_code") or response.status_code != 200:
                error_msg = (
                    getattr(response, "message",
                            "Unknown error") or "Unknown error"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Translation API request failed: {error_msg}",
                )

            # 提取翻译结果
            try:
                if hasattr(response, "output") and hasattr(response.output, "choices"):
                    translated_text = response.output.choices[0].message.content.strip(
                    )
                    if not translated_text:
                        raise ValueError("Empty translation result")

                    return translated_text
                else:
                    raise ValueError("Invalid response format")
            except (AttributeError, IndexError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract translation result: {str(e)}",
                )

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as exc:
            # 记录详细错误信息
            error_detail = f"Translation failed: {type(exc).__name__}: {str(exc)}"
            raise HTTPException(status_code=400, detail=error_detail)

    async def translate_batch(self, text_segments: list) -> list:
        """
        批量翻译多个文本段落，使用特殊分隔符保持一一对应

        Args:
            text_segments: 要翻译的文本段落列表

        Returns:
            翻译后的文本段落列表

        Raises:
            HTTPException: 翻译失败时抛出
        """
        if not text_segments:
            return []

        # 过滤空段落
        non_empty_segments = [seg for seg in text_segments if seg.strip()]
        if not non_empty_segments:
            return text_segments

        try:
            # 使用特殊分隔符连接所有段落
            # 使用 [SEGMENT_SEP] 作为分隔符，这个标记不太可能出现在正常文本中
            separator = "[SEGMENT_SEP]"
            batch_text = separator.join(non_empty_segments)

            # 构建批量翻译提示词
            system_prompt = """
            You are a professional translator assistant specializing in accurate and natural English translations.
            Follow these requirements strictly:
            1. You will receive multiple Chinese text segments separated by [SEGMENT_SEP]
            2. Translate each segment into English independently while:
               - Maintaining the original meaning and intent of each segment
               - Using natural, fluent English expressions
               - Preserving the original tone (formal, casual, technical, etc.)
               - Keeping any specialized terminology accurate
               - For blog content, ensure the translation sounds engaging and natural to native English speakers
            3. Output the translated segments in the SAME ORDER, separated by [SEGMENT_SEP]
            4. Do NOT add explanations, notes, or any extra text
            5. The number of output segments MUST match the number of input segments
            6. Keep the [SEGMENT_SEP] separator EXACTLY as is in your output
            """

            user_prompt = f"Translate the following Chinese segments to English:\n\n{batch_text}"

            # 调用Qwen API进行批量翻译
            response = Generation.call(
                model=self.translation_model,
                api_key=self.api_key,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.translation_max_tokens * 2,  # 批量翻译需要更多tokens
                temperature=self.translation_temperature,
                top_p=self.translation_top_p,
                result_format="message",
            )

            # 检查API响应状态
            if not hasattr(response, "status_code") or response.status_code != 200:
                error_msg = (
                    getattr(response, "message",
                            "Unknown error") or "Unknown error"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch translation API request failed: {error_msg}",
                )

            # 提取翻译结果
            try:
                if hasattr(response, "output") and hasattr(response.output, "choices"):
                    translated_text = response.output.choices[0].message.content.strip(
                    )
                    if not translated_text:
                        raise ValueError("Empty translation result")

                    # 分割翻译结果
                    translated_segments = translated_text.split(separator)

                    # 清理每个段落的首尾空白
                    translated_segments = [seg.strip()
                                           for seg in translated_segments]

                    # 验证段落数量是否匹配
                    if len(translated_segments) != len(non_empty_segments):
                        self.logger.warning(
                            f"Segment count mismatch. Expected {len(non_empty_segments)}, got {len(translated_segments)}")
                        self.logger.warning(
                            f"Original segments: {non_empty_segments}")
                        self.logger.warning(
                            f"Translated segments: {translated_segments}")
                        # 如果数量不匹配，抛出异常让调用者回退到逐段翻译
                        raise ValueError(
                            f"Segment count mismatch: expected {len(non_empty_segments)}, got {len(translated_segments)}")

                    return translated_segments
                else:
                    raise ValueError("Invalid response format")
            except (AttributeError, IndexError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract batch translation result: {str(e)}",
                )

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as exc:
            # 记录详细错误信息
            error_detail = f"Batch translation failed: {type(exc).__name__}: {str(exc)}"
            raise HTTPException(status_code=400, detail=error_detail)

    async def summary(self, content: dict) -> dict:
        """
        使用Qwen API对内容进行总结，生成JSON数组格式的摘要

        Args:
            content: 富文本内容的JSON字典

        Returns:
            包含总结信息的JSON字典：
            - summary: 关键要点数组，每个要点最多255字符

        Raises:
            HTTPException: 总结失败时抛出
        """
        if not content or not isinstance(content, dict):
            raise HTTPException(status_code=404, detail="Content not found")

        # 提取完整文本内容
        extracted_data = self.extract_full_text_from_content(content)
        full_text = extracted_data.get("full_text", "").strip()

        if not full_text:
            raise HTTPException(
                status_code=404, detail="No text content found to summarize")

        try:
            # 构建总结提示词
            system_prompt = """
            You are a professional content analyst and summarizer.
            Your task is to analyze the provided text and generate a structured summary.
            
            Follow these requirements strictly:
            1. Carefully read and understand the entire text
            2. Extract 3-5 key points from the content
            3. Each point should be concise and not exceed 255 characters
            4. Output ONLY a valid JSON object with the following structure:
            {
                "summary": ["first key point", "second key point", "third key point"]
            }
            
            Requirements:
            - The summary field MUST be a JSON array of strings
            - Each string in the array represents one key point
            - Each point should be clear, concise, and capture a key idea
            - Each point MUST NOT exceed 255 characters
            - Use the same language as the input text
            - Output ONLY the JSON object, no additional text or explanations
            """

            user_prompt = f"Analyze and summarize the following text:\n\n{full_text}"

            # 调用Qwen API进行总结
            response = Generation.call(
                model=self.translation_model,
                api_key=self.api_key,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.3,  # 较低的温度以获得更一致的结果
                top_p=0.8,
                result_format="message",
            )

            # 检查API响应状态
            if not hasattr(response, "status_code") or response.status_code != 200:
                error_msg = (
                    getattr(response, "message",
                            "Unknown error") or "Unknown error"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Summary API request failed: {error_msg}",
                )

            # 提取总结结果
            try:
                if hasattr(response, "output") and hasattr(response.output, "choices"):
                    summary_text = response.output.choices[0].message.content.strip(
                    )
                    if not summary_text:
                        raise ValueError("Empty summary result")

                    # 解析JSON结果
                    import json
                    summary_data = json.loads(summary_text)

                    # 验证必需字段
                    if "summary" not in summary_data:
                        raise ValueError("Missing required field: summary")

                    # 验证 summary 是数组
                    summary_content = summary_data["summary"]
                    if not isinstance(summary_content, list):
                        raise ValueError("Summary must be a JSON array")

                    # 确保每个要点不超过 255 字符
                    validated_summary = []
                    for point in summary_content:
                        if isinstance(point, str):
                            if len(point) > 255:
                                # 截断到 255 字符
                                point = point[:252] + "..."
                            validated_summary.append(point)

                    # 直接返回验证后的摘要数组
                    return validated_summary
                else:
                    raise ValueError("Invalid response format")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse summary JSON: {str(e)}. Response: {summary_text[:200]}",
                )
            except (AttributeError, IndexError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract summary result: {str(e)}",
                )

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as exc:
            # 记录详细错误信息
            error_detail = f"Summary generation failed: {type(exc).__name__}: {str(exc)}"
            raise HTTPException(status_code=400, detail=error_detail)

    def extract_full_text_from_content(self, content: dict) -> dict:
        """
        从内容中提取完整文本和媒体caption，为整篇翻译做准备

        Args:
            content: 富文本内容的JSON字典

        Returns:
            包含完整文本内容和媒体caption的字典，用于整篇翻译
        """
        if not content or not isinstance(content, dict):
            return {"full_text": "", "text_parts": [], "media_captions": []}

        text_parts = []
        media_captions = []

        def extract_text_from_node(node, path="", parent_block_type="unknown"):
            """递归提取节点中的文本和媒体caption"""
            if not isinstance(node, dict):
                return

            # 构建当前路径 - 与_replace_text_nodes_by_path保持一致
            node_type = node.get("type", "unknown")
            if path:
                current_path = f"{path}.{node_type}"
            else:
                current_path = node_type

            # 如果是文本节点，检查是否有代码标记
            if node.get("type") == "text":
                # 检查是否有代码标记，如果有则跳过
                marks = node.get("marks", [])
                is_code = False
                for mark in marks:
                    if isinstance(mark, dict) and mark.get("type") == "code":
                        is_code = True
                        break

                if not is_code:  # 只收集非代码文本
                    text = node.get("text", "")
                    # 收集所有非空文本节点（保持原有空格）
                    if text.strip():  # 只检查是否有非空白内容
                        # 使用父级块类型，更准确地反映文本的上下文
                        actual_block_type = parent_block_type if parent_block_type != "unknown" else self._get_block_type_from_path(
                            current_path)

                        # 保留文本的前导和尾随空格信息
                        has_leading_space = text.startswith(" ")
                        has_trailing_space = text.endswith(" ")

                        text_parts.append({
                            "text": text,  # 保持原有空格
                            "path": current_path,
                            "node": node,
                            "block_type": actual_block_type,
                            "has_leading_space": has_leading_space,
                            "has_trailing_space": has_trailing_space
                        })
                return

            # 如果是代码块，直接跳过
            if node.get("type") == "codeBlock":
                return

            # 检查是否是媒体元素（图片、视频、音频）
            if node.get("type") in ["image", "video", "audio"]:
                attrs = node.get("attrs", {})
                caption = attrs.get("caption")
                if caption and caption.strip():
                    media_captions.append({
                        "caption": caption.strip(),
                        "type": node.get("type"),
                        "path": current_path,
                        "node": node
                    })
                return

            # 如果有content字段，递归处理子节点
            if "content" in node and isinstance(node["content"], list):
                # 确定当前节点的块类型
                current_block_type = self._get_block_type_from_path(
                    current_path)
                for i, child in enumerate(node["content"]):
                    child_path = f"{current_path}.content[{i}]"
                    extract_text_from_node(
                        child, child_path, current_block_type)

        # 从根节点开始提取文本
        if "content" in content and isinstance(content["content"], list):
            for i, node in enumerate(content["content"]):
                extract_text_from_node(node, f"content[{i}]")

        # 合并所有文本为完整文档（根据Tiptap JSON结构优化）
        full_text_parts = []
        for i, part in enumerate(text_parts):
            text = part["text"]

            # 对于第一个文本节点，直接添加
            if i == 0:
                full_text_parts.append(text)
                continue

            # 检查前一个文本节点的块类型和当前文本节点的块类型
            prev_part = text_parts[i-1]
            prev_block_type = prev_part.get("block_type", "unknown")
            current_block_type = part.get("block_type", "unknown")

            # 如果是不同的块级元素（如段落、标题等），添加换行符
            if prev_block_type != current_block_type and current_block_type in ["paragraph", "heading", "blockquote", "listItem"]:
                # 确保前一个块以换行符结尾
                if not full_text_parts[-1].endswith("\n"):
                    full_text_parts.append("\n")
            # 如果是同一块内的文本节点，检查是否需要添加空格
            elif prev_block_type == current_block_type:
                prev_text = prev_part["text"]
                # 检查是否需要添加空格
                needs_space = (
                    not prev_text.endswith(" ") and  # 前一个文本不以空格结尾
                    not text.startswith(" ") and     # 当前文本不以空格开头
                    not prev_text.endswith("\n") and  # 前一个文本不以换行符结尾
                    not text.startswith("\n") and    # 当前文本不以换行符开头
                    prev_text.strip() and            # 前一个文本不为空
                    text.strip()                     # 当前文本不为空
                )

                if needs_space:
                    full_text_parts.append(" ")

            full_text_parts.append(text)

        full_text = "".join(full_text_parts)

        return {
            "full_text": full_text,
            "text_parts": text_parts,
            "media_captions": media_captions
        }

    def _get_block_type_from_path(self, path: str) -> str:
        """从路径中提取块级元素类型"""
        # 按优先级顺序检查，避免误匹配
        if "horizontalRule" in path or "hr" in path:
            return "horizontalRule"
        elif "hardBreak" in path or "br" in path:
            return "hardBreak"
        elif "blockquote" in path:
            return "blockquote"
        elif "heading" in path:
            return "heading"
        elif "bulletList" in path or "ul" in path:
            return "bulletList"
        elif "orderedList" in path or "ol" in path:
            return "orderedList"
        elif "listItem" in path or "li" in path:
            return "listItem"
        elif "codeBlock" in path or "pre" in path:
            return "codeBlock"
        elif "image" in path:
            return "image"
        elif "video" in path:
            return "video"
        elif "audio" in path:
            return "audio"
        elif "paragraph" in path:
            return "paragraph"
        else:
            return "unknown"

    async def large_content_translation(self, content: dict) -> dict:
        """
        将富文本内容翻译成英文，保持原有JSON格式，支持媒体caption翻译
        使用批量翻译提高效率，同时保持一一对应关系

        Args:
            content: 富文本内容的JSON字典

        Returns:
            翻译后的JSON字典，保持原有结构
        """
        if not content or not isinstance(content, dict):
            self.logger.warning(
                "Invalid content provided to large_content_translation")
            return content

        # 提取完整文本内容和媒体caption
        extracted_data = self.extract_full_text_from_content(content)
        self.logger.info(
            f"Extracted data: {len(extracted_data.get('text_parts', []))} text parts, {len(extracted_data.get('media_captions', []))} media captions")

        text_parts = extracted_data.get("text_parts", [])
        media_captions = extracted_data.get("media_captions", [])

        if not text_parts and not media_captions:
            self.logger.warning(
                "No text content or media captions found to translate")
            return content  # 如果没有内容需要翻译，直接返回原内容

        try:
            translated_data = {"text_parts": [], "media_captions": []}

            # 批量翻译文本内容 - 提高效率同时保持一一对应
            if text_parts:
                # 批量大小：根据内容长度动态调整
                # 短段落（<100字符）：批量8个
                # 中等段落（100-300字符）：批量5个
                # 长段落（>300字符）：批量3个
                avg_length = sum(len(part["text"])
                                 for part in text_parts) / len(text_parts)
                if avg_length < 100:
                    BATCH_SIZE = 8
                elif avg_length < 300:
                    BATCH_SIZE = 5
                else:
                    BATCH_SIZE = 3

                self.logger.info(
                    f"Starting batch translation: {len(text_parts)} segments, batch size: {BATCH_SIZE}")
                self.logger.info(
                    f"Average segment length: {avg_length:.0f} characters")

                # 分批处理
                for batch_start in range(0, len(text_parts), BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, len(text_parts))
                    batch = text_parts[batch_start:batch_end]

                    self.logger.info(
                        f"Translating batch {batch_start//BATCH_SIZE + 1}/{(len(text_parts) + BATCH_SIZE - 1)//BATCH_SIZE} (segments {batch_start+1}-{batch_end})")

                    # 提取批次中的文本
                    batch_texts = [part["text"] for part in batch]

                    try:
                        # 批量翻译
                        translated_texts = await self.translate_batch(batch_texts)

                        # 验证翻译结果数量
                        if len(translated_texts) != len(batch):
                            self.logger.warning(
                                "Batch translation count mismatch, falling back to individual translation")
                            # 回退到逐段翻译
                            translated_texts = []
                            for text in batch_texts:
                                try:
                                    translated = await self.translate(text)
                                    translated_texts.append(translated)
                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to translate segment: {e}")
                                    # 翻译失败，保留原文
                                    translated_texts.append(text)

                        # 构建翻译结果
                        for orig_part, translated_text in zip(batch, translated_texts):
                            translated_data["text_parts"].append({
                                "text": translated_text,
                                "path": orig_part["path"],
                                "node": orig_part["node"],
                                "block_type": orig_part.get("block_type", "unknown")
                            })

                        self.logger.info(
                            f"Batch translation completed: {len(translated_texts)} segments")

                    except Exception as e:
                        self.logger.error(
                            f"Batch translation failed: {e}, falling back to individual translation")
                        # 批量翻译失败，回退到逐段翻译
                        for text_part in batch:
                            original_text = text_part["text"]
                            try:
                                translated_text = await self.translate(original_text)
                                translated_data["text_parts"].append({
                                    "text": translated_text,
                                    "path": text_part["path"],
                                    "node": text_part["node"],
                                    "block_type": text_part.get("block_type", "unknown")
                                })
                            except Exception as e2:
                                self.logger.error(
                                    f"Failed to translate segment: {e2}")
                                # 如果单个段落翻译也失败，保留原文
                                translated_data["text_parts"].append({
                                    "text": original_text,
                                    "path": text_part["path"],
                                    "node": text_part["node"],
                                    "block_type": text_part.get("block_type", "unknown")
                                })

            # 批量翻译媒体caption
            if media_captions:
                self.logger.info(
                    f"Starting batch translation of {len(media_captions)} media captions")

                # Caption通常较短，使用较大的批量大小
                CAPTION_BATCH_SIZE = 10

                for batch_start in range(0, len(media_captions), CAPTION_BATCH_SIZE):
                    batch_end = min(
                        batch_start + CAPTION_BATCH_SIZE, len(media_captions))
                    batch = media_captions[batch_start:batch_end]

                    self.logger.info(
                        f"Translating caption batch {batch_start//CAPTION_BATCH_SIZE + 1} (captions {batch_start+1}-{batch_end})")

                    # 提取批次中的caption文本
                    batch_captions = [item["caption"] for item in batch]

                    try:
                        # 批量翻译caption
                        translated_captions = await self.translate_batch(batch_captions)

                        # 验证翻译结果数量
                        if len(translated_captions) != len(batch):
                            self.logger.warning(
                                "Caption batch translation count mismatch, falling back to individual translation")
                            # 回退到逐个翻译
                            translated_captions = []
                            for caption in batch_captions:
                                try:
                                    translated = await self.translate(caption)
                                    translated_captions.append(translated)
                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to translate caption: {e}")
                                    # 翻译失败，保留原文
                                    translated_captions.append(caption)

                        # 构建翻译结果
                        for orig_item, translated_caption in zip(batch, translated_captions):
                            translated_data["media_captions"].append({
                                "caption": translated_caption,
                                "type": orig_item["type"],
                                "path": orig_item["path"],
                                "node": orig_item["node"]
                            })

                        self.logger.info(
                            f"Caption batch translation completed: {len(translated_captions)} captions")

                    except Exception as e:
                        self.logger.error(
                            f"Caption batch translation failed: {e}, falling back to individual translation")
                        # 批量翻译失败，回退到逐个翻译
                        for caption_item in batch:
                            try:
                                translated_caption = await self.translate(caption_item["caption"])
                                translated_data["media_captions"].append({
                                    "caption": translated_caption,
                                    "type": caption_item["type"],
                                    "path": caption_item["path"],
                                    "node": caption_item["node"]
                                })
                            except Exception as e2:
                                self.logger.error(
                                    f"Failed to translate caption: {e2}")
                                # 如果caption翻译失败，保留原文
                                translated_data["media_captions"].append({
                                    "caption": caption_item["caption"],
                                    "type": caption_item["type"],
                                    "path": caption_item["path"],
                                    "node": caption_item["node"]
                                })

            # 标准化翻译后的内容空格
            self.logger.info("Normalizing spacing in translated content")

            # 标准化文本段落
            if "text_parts" in translated_data:
                for part in translated_data["text_parts"]:
                    if isinstance(part, dict) and "text" in part:
                        part["text"] = self._normalize_english_spacing(
                            part["text"])

            # 标准化媒体caption
            if "media_captions" in translated_data:
                for caption in translated_data["media_captions"]:
                    if isinstance(caption, dict) and "caption" in caption:
                        caption["caption"] = self._normalize_english_spacing(
                            caption["caption"])

            # 将翻译后的内容替换回原JSON结构中
            translated_content = self._replace_translated_content(
                content, extracted_data, translated_data)

            self.logger.info(
                f"Translation completed successfully: {len(translated_data['text_parts'])} text segments, {len(translated_data['media_captions'])} captions")

            return translated_content

        except Exception as exc:
            # 如果翻译失败，记录错误并重新抛出异常
            self.logger.error(f"Translation failed: {exc}")
            self.logger.error(f"Exception type: {type(exc).__name__}")
            # 重新抛出异常而不是返回原内容，让调用者知道翻译失败
            raise

    def _replace_translated_content(self, content: dict, extracted_data: dict, translated_data: dict) -> dict:
        """
        在JSON结构中替换逐段翻译的文本内容和媒体caption

        Args:
            content: 原始JSON内容
            extracted_data: 提取的原始文本和媒体caption数据
            translated_data: 翻译后的文本和媒体caption数据

        Returns:
            替换后的JSON内容
        """
        import copy

        # 深拷贝避免修改原内容
        result = copy.deepcopy(content)

        # 替换文本内容 - 使用路径精确匹配
        text_parts = extracted_data.get("text_parts", [])
        translated_parts = translated_data.get("text_parts", [])

        # 创建路径到翻译文本的映射，智能处理英文空格
        path_to_translation = {}
        for i, (orig_part, trans_part) in enumerate(zip(text_parts, translated_parts)):
            if orig_part["text"].strip() and trans_part["text"].strip():
                # 先标准化翻译文本，确保内部只有单个空格
                translated_text = self._normalize_english_spacing(
                    trans_part["text"])

                # 对于英文翻译，需要智能添加空格
                # 检查是否需要前导空格
                needs_leading_space = False
                if i > 0:  # 不是第一个节点
                    prev_part = text_parts[i - 1]
                    # 如果前一个节点和当前节点在同一个块中，且前一个节点有内容
                    if prev_part.get("block_type") == orig_part.get("block_type"):
                        # 英文单词之间需要空格
                        needs_leading_space = True

                # 检查是否需要尾随空格
                needs_trailing_space = False
                if i < len(text_parts) - 1:  # 不是最后一个节点
                    next_part = text_parts[i + 1]
                    # 如果下一个节点和当前节点在同一个块中
                    if next_part.get("block_type") == orig_part.get("block_type"):
                        # 英文单词之间需要空格
                        needs_trailing_space = True

                # 如果原文有空格，优先使用原文的空格信息
                if orig_part.get("has_leading_space", False):
                    needs_leading_space = True
                if orig_part.get("has_trailing_space", False):
                    needs_trailing_space = True

                # 添加标准的单个空格
                if needs_leading_space:
                    translated_text = " " + translated_text
                if needs_trailing_space:
                    translated_text = translated_text + " "

                path_to_translation[orig_part["path"]] = translated_text

        # 替换媒体caption - 使用路径精确匹配
        media_captions = extracted_data.get("media_captions", [])
        translated_media_captions = translated_data.get("media_captions", [])

        # 创建路径到翻译caption的映射
        path_to_caption = {}
        for orig, trans in zip(media_captions, translated_media_captions):
            if orig["caption"].strip() and trans["caption"].strip():
                # 保持翻译caption的原始空格结构
                path_to_caption[orig["path"]] = trans["caption"]

        # 执行替换 - 从content开始，跳过根节点
        if "content" in result and isinstance(result["content"], list):
            for i, child in enumerate(result["content"]):
                child_path = f"content[{i}]"
                self._replace_text_nodes_by_path(
                    child, path_to_translation, child_path)

        if "content" in result and isinstance(result["content"], list):
            for i, child in enumerate(result["content"]):
                child_path = f"content[{i}]"
                self._replace_media_captions_by_path(
                    child, path_to_caption, child_path)

        return result

    def _replace_text_nodes_by_path(self, node: dict, path_to_translation: dict, current_path: str = ""):
        """根据路径递归替换文本节点"""
        if not isinstance(node, dict):
            return

        # 构建当前路径 - 与extract_text_from_node保持一致
        node_type = node.get("type", "unknown")
        if current_path:
            current_path = f"{current_path}.{node_type}"
        else:
            current_path = node_type

        # 如果是文本节点，检查路径匹配
        if node.get("type") == "text":
            if current_path in path_to_translation:
                node["text"] = path_to_translation[current_path]
            return

        # 如果是代码块，跳过
        if node.get("type") == "codeBlock":
            return

        # 递归处理子节点
        if "content" in node and isinstance(node["content"], list):
            for i, child in enumerate(node["content"]):
                child_path = f"{current_path}.content[{i}]"
                self._replace_text_nodes_by_path(
                    child, path_to_translation, child_path)

    def _replace_media_captions_by_path(self, node: dict, path_to_caption: dict, current_path: str = ""):
        """根据路径递归替换媒体caption"""
        if not isinstance(node, dict):
            return

        # 构建当前路径 - 与extract_text_from_node保持一致
        node_type = node.get("type", "unknown")
        if current_path:
            current_path = f"{current_path}.{node_type}"
        else:
            current_path = node_type

        # 如果是媒体元素，检查路径匹配并替换caption
        if node.get("type") in ["image", "video", "audio"]:
            if current_path in path_to_caption:
                attrs = node.get("attrs", {})
                attrs["caption"] = path_to_caption[current_path]
            return

        # 递归处理子节点
        if "content" in node and isinstance(node["content"], list):
            for i, child in enumerate(node["content"]):
                child_path = f"{current_path}.content[{i}]"
                self._replace_media_captions_by_path(
                    child, path_to_caption, child_path)


agent_utils = AgentUtils()
