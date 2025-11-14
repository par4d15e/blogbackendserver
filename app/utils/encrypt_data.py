import base64
import json
import zlib
from typing import Dict, Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESJsonCipher:
    """
    提供 JSON 数据的压缩 + AES-CBC 加密 + Base64 编码的加解密工具
    """

    def __init__(self, key: bytes):
        """
        :param key: AES 密钥 (16/24/32 字节)
        """
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be either 16, 24, or 32 bytes long.")
        self.key = key

    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        对 JSON 数据进行压缩 + AES-CBC 加密 + Base64 编码
        :param data: 原始 dict 数据
        :return: 加密后的字符串
        """
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode("utf-8"))

        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(compressed, AES.block_size))

        encrypted_data = cipher.iv + ct_bytes
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypt(self, token: str) -> Dict[str, Any]:
        """
        解密加密后的字符串，恢复原始 JSON 数据
        :param token: 加密后的字符串
        :return: 解密还原后的 dict 数据
        """
        decoded = base64.b64decode(token.encode("utf-8"))
        iv = decoded[:16]
        ct = decoded[16:]

        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decompressed = unpad(cipher.decrypt(ct), AES.block_size)
        json_str = zlib.decompress(decompressed).decode("utf-8")

        return json.loads(json_str)
