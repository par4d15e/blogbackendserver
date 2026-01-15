from fastapi import Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select
from fastapi.security import APIKeyCookie

from app.core.database.mysql import mysql_manager
from app.core.database.redis import redis_manager
from app.core.security import security_manager
from app.crud.auth_crud import get_auth_crud
from app.models.auth_model import RefreshToken
from app.core.logger import logger_manager
from app.core.config.settings import settings


get_access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,
    scheme_name="Bearer",
    description="Access token for authentication",
)

get_refresh_token_cookie = APIKeyCookie(
    name="refresh_token",
    auto_error=False,
    scheme_name="Bearer",
    description="Refresh token for authentication",
)


class Dependencies:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_crud = get_auth_crud(db)
        self.redis_manager = redis_manager
        self.postgresql_manager = mysql_manager
        self.security_manager = security_manager
        self.logger = logger_manager.get_logger(__name__)

    async def get_current_user(
        self,
        access_token: str = Depends(get_access_token_cookie),
        db: AsyncSession = Depends(mysql_manager.get_db),
    ):
        self.logger.info(
            f"get_current_user called with access_token: {'***' if access_token else 'None'}"
        )

        if not access_token:
            self.logger.warning("No access_token provided in request")
            raise HTTPException(
                status_code=401,
                detail="Unauthorized access",
            )

        # 使用 JWT 验证 access_token（不查询数据库）
        try:
            self.logger.info("Attempting to decode access token")
            token_data = security_manager.decode_token(access_token)
            if token_data:
                self.logger.info(
                    f"Token decoded successfully, user_id: {token_data.get('user_id')}"
                )
                user_id = token_data.get("user_id")
                jti = token_data.get("jti")

                if user_id and jti:
                    # 检查 token 是否在黑名单中（已登出）
                    try:
                        is_blacklisted = await redis_manager.exists_async(
                            f"blacklist:access_token:{jti}"
                        )
                        if is_blacklisted:
                            self.logger.warning(
                                f"Access token {jti} is blacklisted (user logged out)"
                            )
                            raise HTTPException(
                                status_code=401,
                                detail="Token has been revoked",
                            )
                    except HTTPException:
                        raise
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to check token blacklist: {e}, allowing request"
                        )
                        # 如果 Redis 不可用，允许请求通过（降级策略）

                    # 从数据库中获取用户信息
                    user = await self.auth_crud.get_user_by_id(user_id)
                    if (
                        user
                        and user.is_active
                        and user.is_verified
                        and not user.is_deleted
                    ):
                        self.logger.info(
                            f"User authenticated via access token: {user.email}"
                        )
                        return user
                    else:
                        self.logger.warning(
                            f"User validation failed - active: {user.is_active if user else 'N/A'}, verified: {user.is_verified if user else 'N/A'}, deleted: {user.is_deleted if user else 'N/A'}"
                        )
                else:
                    self.logger.warning("No user_id or jti found in decoded token")
            else:
                self.logger.warning("Token decode returned None")
        except HTTPException:
            raise
        except Exception as e:
            self.logger.warning(f"Access token validation failed: {str(e)}")

        # 如果token验证失败，抛出未授权错误
        self.logger.warning("Token validation failed")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
        )

    async def cleanup_tokens(
        self,
        response: Response,
    ) -> bool:
        """Cleanup user tokens on logout."""
        response.delete_cookie(
            "access_token",
            domain=settings.domain.COOKIE_DOMAIN,
            path="/",
        )
        self.logger.info("Access token cookie deleted")
        response.delete_cookie(
            "refresh_token",
            domain=settings.domain.COOKIE_DOMAIN,
            path="/",
        )
        self.logger.info("Refresh token cookie deleted")
        return True
