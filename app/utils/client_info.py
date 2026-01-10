import httpx
from typing import Optional, Dict
from fastapi import Request
from app.core.logger import logger_manager


class ClientInfoUtils:
    """客户端信息获取服务"""

    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)

    def get_client_ip(self, request: Request) -> Optional[str]:
        """获取客户端真实IP地址"""
        # 优先检查 Cloudflare 的真实 IP header
        possible_headers = [
            "CF-Connecting-IP",  # Cloudflare 真实客户端IP (最优先)
            "True-Client-IP",  # Cloudflare Enterprise
            "X-Forwarded-For",  # 标准代理header,取第一个IP
            "X-Real-IP",  # Nginx等代理
            "X-Client-IP",
        ]

        for header in possible_headers:
            ip = request.headers.get(header)
            if ip and ip.lower() != "unknown":
                ip = ip.split(",")[0].strip()
                return ip

        return request.client.host if request.client else None

    def get_client_ip_from_headers(self, headers: dict) -> Optional[str]:
        """从请求头字典中获取客户端真实IP地址（用于Celery任务）"""

        # 将headers的key转换为小写,以便不区分大小写匹配
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # 优先检查 Cloudflare 的真实 IP header (使用小写key)
        possible_headers = [
            "cf-connecting-ip",  # Cloudflare 真实客户端IP (最优先)
            "true-client-ip",  # Cloudflare Enterprise
            "x-forwarded-for",  # 标准代理header,取第一个IP
            "x-real-ip",  # Nginx等代理
            "x-client-ip",
        ]

        for header in possible_headers:
            ip = headers_lower.get(header)
            if ip and ip.lower() != "unknown":
                ip = ip.split(",")[0].strip()
                self.logger.info(f"从 {header} 解析出的IP: {ip}")
                return ip

        self.logger.warning("未能从请求头中解析出客户端IP")
        return None

    def get_ip_location(self, ip: Optional[str]) -> Dict:
        """获取 IP 地址的地理位置信息"""
        url = f"https://ipinfo.io/{ip}/json"
        try:
            with httpx.Client(timeout=3.0) as client:  # 减少超时时间到3秒
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    loc = data.get("loc", "").split(",")
                    return {
                        "city": data.get("city", "未知"),
                        "longitude": float(loc[1]) if len(loc) == 2 else None,
                        "latitude": float(loc[0]) if len(loc) == 2 else None,
                    }
        except Exception as e:
            self.logger.error(f"获取 IP 地理信息失败: {e}")

        return {"city": "beijing", "longitude": "116.3971", "latitude": "39.9075"}

    def get_location_by_long_lat(self, lat: float, lon: float) -> Dict:
        """根据经纬度反查位置"""
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        try:
            with httpx.Client(timeout=3.0) as client:  # 减少超时时间到3秒
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "city": data.get("address", {}).get("city", "未知"),
                        "country": data.get("address", {}).get("country", "未知"),
                    }
        except Exception as e:
            self.logger.error(f"获取地理位置信息失败: {e}")

        return {"city": "未知", "country": "未知"}

    def get_user_agent(self, request: Request) -> Optional[str]:
        """获取客户端浏览器信息"""
        return request.headers.get("User-Agent")


client_info_utils = ClientInfoUtils()
