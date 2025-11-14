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
        possible_headers = [
            "X-Real-IP",
            "X-Forwarded-For",
            "CF-Connecting-IP",
            "X-Client-IP",
            "True-Client-IP",
        ]

        for header in possible_headers:
            ip = request.headers.get(header)
            if ip and ip.lower() != "unknown":
                ip = ip.split(",")[0].strip()
                return ip

        return request.client.host if request.client else None

    def get_client_ip_from_headers(self, headers: dict) -> Optional[str]:
        """从请求头字典中获取客户端真实IP地址（用于Celery任务）"""
        possible_headers = [
            "X-Real-IP",
            "X-Forwarded-For",
            "CF-Connecting-IP",
            "X-Client-IP",
            "True-Client-IP",
        ]

        for header in possible_headers:
            ip = headers.get(header)
            if ip and ip.lower() != "unknown":
                ip = ip.split(",")[0].strip()
                return ip

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
