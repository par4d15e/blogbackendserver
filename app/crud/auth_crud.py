import uuid
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends
from sqlalchemy import exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload
from sqlmodel import select, delete, or_, update, func, insert
from celery import chain
from app.models.auth_model import (
    Code,
    CodeType,
    Token,
    TokenType,
    Social_Account,
    SocialProvider,
)
from app.models.user_model import User, RoleType
from app.models.media_model import Media, MediaType
from app.core.logger import logger_manager
from app.core.security import security_manager
from app.core.config.settings import settings
from app.core.database.mysql import mysql_manager
from app.core.database.redis import redis_manager
from app.core.i18n.i18n import get_message, Language
from app.crud.subscriber_crud import get_subscriber_crud
from app.tasks.client_info_task import client_info_task
from app.tasks.greeting_email_task import greeting_email_task


class AuthCrud:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger_manager.get_logger(__name__)

    async def _get_user_by_username(self, username: str) -> bool:
        """Get user by username - 新增方法，利用索引"""
        statement = select(exists(select(User.id)).where(
            User.username == username))
        result = await self.db.execute(statement)
        return bool(result.scalar_one())

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email specifically for login - 使用复合索引优化"""
        statement = (
            select(User)
            .options(
                # 禁用所有关系的自动加载，只查询User表本身
                lazyload("*")
            )
            .where(
                User.email == email,
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by id."""
        statement = (
            select(User)
            .options(
                # 禁用所有关系的自动加载，只查询User表本身
                lazyload("*")
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def _get_valid_code(self, user_id: int, type: CodeType) -> Optional[Code]:
        """获取有效的验证码"""
        statement = select(Code).where(
            Code.user_id == user_id,
            Code.type == type,
            Code.expires_at > func.utc_timestamp(),
            Code.is_used == False,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def _validate_code(
        self, user_id: int, code: str, type: CodeType
    ) -> Optional[Code]:
        """验证code是否有效"""
        statement = select(Code).where(
            Code.user_id == user_id,
            Code.code == code,
            Code.type == type,
            Code.expires_at > func.utc_timestamp(),
            Code.is_used == False,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def _create_default_avatar(
        self, user_id: int, avatar_url: Optional[str] = None
    ) -> Media:
        """Create default avatar for user."""
        if not avatar_url:
            avatar_url = f"{settings.domain.DOMAIN_URL}/static/image/default_avatar.png"
        else:
            avatar_url = avatar_url

        media = Media(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            type=MediaType.image,
            is_avatar=True,
            file_name=f"avatar_{user_id}.png",
            original_filepath_url=avatar_url,
            thumbnail_filepath_url=avatar_url,
            watermark_filepath_url=avatar_url,
        )
        self.db.add(media)
        await self.db.flush()  # 获取自增ID
        return media

    async def _update_user_and_code(
        self,
        user: User,
        username: str,
        password_hash: str,
        valid_code: Code,
    ):
        """Update user information and mark verification code as used."""
        # 更新验证码状态
        valid_code.is_used = True
        self.db.add(valid_code)

        # 更新用户信息
        user.username = username
        user.password_hash = password_hash
        user.is_verified = True
        user.is_active = True  # 激活用户账户
        self.db.add(user)

        # 提交所有更改
        await self.db.commit()

    async def _get_user_tokens(self, user_id: int) -> List[Token]:
        """Get all valid tokens for user - 优化查询"""
        statement = (
            select(Token)
            .options(lazyload("*"))
            .where(
                Token.user_id == user_id,
                Token.expired_at > func.utc_timestamp(),
                Token.is_active == True,
            )
        )
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def _revoke_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for user"""
        statement = (
            update(Token)
            .where(Token.user_id == user_id, Token.is_active == True)
            .values(is_active=False)
        )
        result = await self.db.execute(statement)
        await self.db.commit()
        return (result.rowcount or 0) > 0

    async def _cleanup_tokens(self, user_id: int) -> int:
        """
        清理已过期或未激活的 Token
        """
        statement = delete(Token).where(
            Token.user_id == user_id,
            or_(func.utc_timestamp() >= Token.expired_at,
                Token.is_active == False),
        )
        result = await self.db.execute(statement)
        await self.db.commit()
        return result.rowcount

    async def _save_token_to_database(
        self, user_id: int, jit: str, type: TokenType, token: str, expired_at: datetime
    ) -> Token:
        """Create a new token."""
        new_token = await self.db.execute(
            insert(Token).values(
                user_id=user_id, jit=jit, type=type, token=token, expired_at=expired_at
            )
        )
        await self.db.commit()
        return new_token

    async def _generate_tokens_by_condition(
        self, user_id: int, email: str, role: RoleType, username: str
    ) -> Dict[str, str]:
        """根据条件生成访问令牌和刷新令牌"""
        # 一次性查询所有有效的tokens
        valid_tokens = await self._get_user_tokens(user_id)
        # 高效分类token - 使用字典推导式
        token_dict = {token.type: token for token in valid_tokens}
        existing_access_token = token_dict.get(TokenType.access)
        existing_refresh_token = token_dict.get(TokenType.refresh)

        # 定期清理过期token
        await self._cleanup_tokens(user_id)

        # 检查token状态并智能处理
        if existing_access_token and existing_refresh_token:
            # 如果access和refresh token都有效，直接返回
            self.logger.info(
                f"User {email} already has valid tokens after social login."
            )
            return {
                "access_token": existing_access_token.token,
                "refresh_token": existing_refresh_token.token,
            }
        elif existing_refresh_token and not existing_access_token:
            # refresh_token有效，access_token无效 - 用refresh_token生成新的access_token
            self.logger.info(
                f"User {email} has valid refresh token after social login, generating new access token."
            )
            access_jti = str(uuid.uuid4())
            refresh_jti = existing_refresh_token.jit  # 保持现有的refresh_token

            shared_payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": role,
            }

            access_token_data = {**shared_payload, "jti": access_jti}
            access_token, access_token_expired_at = (
                security_manager.create_access_token(access_token_data)
            )

            # 只保存新的access_token
            await self._save_token_to_database(
                user_id=user_id,
                jit=access_jti,
                type=TokenType.access,
                token=access_token,
                expired_at=access_token_expired_at,
            )

            return {
                "access_token": access_token,
                "refresh_token": existing_refresh_token.token,
            }

        elif existing_access_token and not existing_refresh_token:
            # access_token有效，refresh_token无效 - 用access_token生成新的refresh_token
            self.logger.info(
                f"User {email} has valid access token after social login, generating new refresh token."
            )
            access_jti = existing_access_token.jit  # 保持现有的access_token
            refresh_jti = str(uuid.uuid4())

            shared_payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": role,
            }

            refresh_token_data = {**shared_payload, "jti": refresh_jti}
            refresh_token, refresh_token_expired_at = (
                security_manager.create_refresh_token(refresh_token_data)
            )

            # 只保存新的refresh_token
            await self._save_token_to_database(
                user_id=user_id,
                jit=refresh_jti,
                type=TokenType.refresh,
                token=refresh_token,
                expired_at=refresh_token_expired_at,
            )

            return {
                "access_token": existing_access_token.token,
                "refresh_token": refresh_token,
            }

        # 两个token都无效，生成全新的token对
        self.logger.info(
            f"User {email} needs new token pair after social login.")
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        shared_payload = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "role": role,
        }

        access_token_data = {**shared_payload, "jti": access_jti}
        refresh_token_data = {**shared_payload, "jti": refresh_jti}

        access_token, access_token_expired_at = (
            security_manager.create_access_token(access_token_data)
        )
        refresh_token, refresh_token_expired_at = (
            security_manager.create_refresh_token(refresh_token_data)
        )

        # 保存令牌（一次提交）
        await self._save_token_to_database(
            user_id=user_id,
            jit=access_jti,
            type=TokenType.access,
            token=access_token,
            expired_at=access_token_expired_at,
        )
        await self._save_token_to_database(
            user_id=user_id,
            jit=refresh_jti,
            type=TokenType.refresh,
            token=refresh_token,
            expired_at=refresh_token_expired_at,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    async def _get_social_account(self, user_id: int) -> Optional[Social_Account]:
        """Get social account by user_id."""
        statement = (
            select(Social_Account)
            .options(lazyload("*"))
            .where(
                Social_Account.user_id == user_id,
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_code_crud(
        self, email: str, type: CodeType, code: str, language: Language
    ) -> Code:
        """Create code for user by type.
        两种类型都会对未过期且未使用的验证码进行限流。
        """
        try:
            # 查找用户
            user = await self.get_user_by_email(email)

            # reset 流程不允许为不存在用户创建账号
            if not user and type == CodeType.reset:
                raise HTTPException(
                    status_code=404,
                    detail=get_message(
                        key="auth.common.userNotFound", lang=language),
                )

            # verified 流程在用户不存在时创建占位用户
            if not user and type == CodeType.verified:
                user = User(email=email)
                self.db.add(user)
                await self.db.flush()

            # 至此 user 一定存在
            if user.is_deleted:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.common.userDeleted", lang=language),
                )

            # verified: 已激活已验证的用户不应再次发送注册验证码
            if type == CodeType.verified and user.is_active and user.is_verified:
                raise HTTPException(
                    status_code=409,
                    detail=get_message(
                        key="auth.common.userExists", lang=language),
                )

            # reset: 仅允许已激活且已验证的用户
            if type == CodeType.reset:
                if not user.is_active:
                    raise HTTPException(
                        status_code=400,
                        detail=get_message(
                            key="auth.common.userNotActive", lang=language
                        ),
                    )
                if not user.is_verified:
                    raise HTTPException(
                        status_code=400,
                        detail=get_message(
                            key="auth.common.userNotVerified", lang=language
                        ),
                    )

            # 限流：若已有有效验证码，则拒绝重复发送
            existing_valid_code = await self._get_valid_code(user.id, type)
            if existing_valid_code:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.common.validationCodeAlreadyRequested", lang=language
                    ),
                )

            # 创建新的验证码
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.email.EMAIL_EXPIRATION // 60
            )

            # Create the Code model instance
            code_obj = Code(
                user_id=user.id,
                code=code,
                type=type,
                expires_at=expires_at,
            )

            self.db.add(code_obj)
            await self.db.commit()
            await self.db.refresh(code_obj)

            self.logger.info(f"Verification code created for user: {email}")
            return code_obj

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            self.logger.error(
                f"Error creating verification code for {email}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating verification code for {email}: {str(e)}",
            )

    async def create_user_account(
        self,
        email: str,
        username: str,
        password_hash: str,
        code: str,
        type: CodeType,
        language: Language,
    ) -> bool:
        """Create a new user account with verification code validation."""
        try:
            # 查找用户和验证码（使用单个查询优化）
            user = await self.get_user_by_email(email)

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=get_message(
                        key="auth.common.userNotFound", lang=language),
                )
            # 检查用户是否已删除
            elif user.is_deleted:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.common.userDeleted", lang=language),
                )

            # 检查用户是否已经激活和验证
            elif user.is_active and user.is_verified and not user.is_deleted:
                raise HTTPException(
                    status_code=409,
                    detail=get_message(
                        key="auth.common.userExists", lang=language),
                )

            # 验证验证码
            valid_code = await self._validate_code(user.id, code, type)
            if not valid_code:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.common.invalidVerificationCode", lang=language
                    ),
                )

            # 检查用户名是否已存在
            if await self._get_user_by_username(username):
                raise HTTPException(
                    status_code=409,
                    detail=get_message(
                        key="auth.common.userNameAlreadyExists", lang=language
                    ),
                )

            # 创建默认头像
            await self._create_default_avatar(user.id)

            # 更新用户信息和验证码状态（在单个事务中）
            await self._update_user_and_code(
                user=user,
                username=username,
                password_hash=password_hash,
                valid_code=valid_code,
            )

            # 添加用户到订阅者列表
            # 使用 ensure_subscriber_active 确保订阅者存在且激活
            subscriber_crud = get_subscriber_crud(self.db)
            await subscriber_crud.ensure_subscriber_active(user.email)

            self.logger.info(f"User account created successfully: {email}")

            # 清理user list缓存
            await redis_manager.delete_pattern_async("admin_all_users:page=*")

            return True

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            self.logger.error(
                f"Error creating user account for {email}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating user account for {email}: {str(e)}",
            )

    async def reset_user_password(
        self, email: str, new_password: str, code: str, language: Language
    ) -> bool:
        """Reset user password."""
        # 查找用户
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="auth.common.userNotFound", lang=language),
            )

        # 检查用户是否已删除
        elif user and user.is_deleted:
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.userDeleted", lang=language),
            )

        elif user and not user.is_active and not user.is_verified:
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.userNotVerified", lang=language),
            )

        # 检验密码是否一样
        if security_manager.verify_password(new_password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.passwordSameAsOld", lang=language),
            )

        # 加密新密码
        new_password_hash = security_manager.hash_password(new_password)

        # 检查用户是否已激活
        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.userNotActive", lang=language),
            )
        # 检查用户是否已验证
        if not user.is_verified:
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.userNotVerified", lang=language),
            )

        # 验证验证码
        valid_code = await self._validate_code(user.id, code, CodeType.reset)
        if not valid_code:
            raise HTTPException(
                status_code=400,
                detail=get_message(
                    key="auth.common.invalidVerificationCode", lang=language
                ),
            )

        # 更新密码
        statement = (
            update(User)
            .where(User.id == user.id)
            .values(password_hash=new_password_hash)
        )
        await self.db.execute(statement)
        statement = update(Code).where(
            Code.id == valid_code.id).values(is_used=True)
        await self.db.execute(statement)
        await self.db.commit()

        self.logger.info(f"Password reset successfully for user: {email}")
        return True

    async def reset_logged_in_user_password(
        self, user_email: str, new_password: str, language: Language
    ) -> bool:
        """Reset logged in user password"""
        # 由于用户已经登陆进来，所以完全可以直接更新password
        if security_manager.validate_password(new_password):
            # 查找用户
            user = await self.get_user_by_email(user_email)
            if user and user.password_hash:
                # 验证新密码是否和数据库中的密码是否一样
                if security_manager.verify_password(
                    new_password, user.password_hash
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=get_message(
                            key="auth.common.passwordSameAsOld", lang=language
                        ),
                    )

            # hash password
            hashed_password = security_manager.hash_password(new_password)
            statement = (
                update(User)
                .where(User.email == user_email)
                .values(password_hash=hashed_password)
            )
            await self.db.execute(statement)
            await self.db.commit()
            return True
        return False

    async def account_login(
        self, request, email: str, password: str, language: Language
    ) -> Dict[str, str]:
        """User account login - 高性能优化版本"""

        try:
            # 1. 优化查询：使用专门的登录查询方法，一次性验证所有登录条件
            user = await self.get_user_by_email(email)

            # 2. 验证用户存在性和密码
            if not user:
                # 用户不存在
                raise HTTPException(
                    status_code=404,
                    detail=get_message(
                        key="auth.common.userNotFound", lang=language),
                )
            # 3. 用户已被删除
            elif user.is_deleted:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.common.userDeleted", lang=language),
                )

            # 4. 验证用户是否是social account
            user_social_account = await self.db.execute(
                select(Social_Account)
                .options(
                    lazyload("*"),
                )
                .where(Social_Account.user_id == user.id)
            )
            user_social_account = user_social_account.scalar_one_or_none()
            if user.password_hash is None and user_social_account:
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.accountLogin.socialAccountNotAllowed", lang=language
                    ),
                )

            # 5. 验证密码
            if not security_manager.verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=400,
                    detail=get_message(
                        key="auth.accountLogin.invalidCredentials", lang=language
                    ),
                )

            # 6. 智能生成令牌
            tokens = await self._generate_tokens_by_condition(
                user_id=user.id,
                email=user.email,
                role=user.role,
                username=user.username,
            )

            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            # 异步后台任务：发送欢迎邮件 → 更新客户端信息（顺序执行，非阻塞）
            try:
                if (
                    not user.ip_address
                    or not user.city
                    or not user.latitude
                    or not user.longitude
                ):
                    # 先发欢迎邮件（延迟10秒），完成后再更新客户端信息
                    task_flow = chain(
                        greeting_email_task.s(user.email, language.value).set(
                            countdown=10
                        ),
                        # 使用 si 确保不接收上一个任务的返回值
                        client_info_task.si(user.id, dict(request.headers)),
                    )
                    task_flow.apply_async()
                    self.logger.info(
                        f"Chained tasks: greeting → client info for {user.email}"
                    )
                else:
                    # 无需欢迎邮件，直接更新客户端信息（保持10秒延迟以与先前逻辑一致）
                    headers_dict = dict(request.headers)
                    self.logger.info(f"🔍 准备传递给Celery的headers: {headers_dict}")
                    client_info_task.apply_async(
                        args=[user.id, headers_dict], countdown=10
                    )
            except Exception as e:
                self.logger.warning(f"启动任务失败: {e}")

            # 7. 返回响应
            return {"access_token": access_token, "refresh_token": refresh_token}

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Login error for user {email}: {str(e)}")
            try:
                await self.db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Login error for user {email}: {str(e)}",
            )

    async def account_logout(self, user_id: int) -> bool:
        """User account logout - 撤销用户所有token"""
        # 获取用户信息
        user = await self.get_user_by_id(user_id)
        if user and user.is_active and user.is_verified and not user.is_deleted:
            # 删除用户所有token
            revoked = await self._revoke_user_tokens(user_id)
            if revoked:
                self.logger.info(
                    f"User {user.email} tokens revoked successfully.")
                return True
            else:
                self.logger.warning(
                    f"No active tokens found for user {user.email}.")
                return False
        else:
            self.logger.warning("User not found or ID mismatch.")
            return False

    async def generate_access_token(
        self, user_id: int, email: str, jit: str, language: Language
    ) -> str:
        """Generate access token for user"""
        # 检查是否有真实的用户
        user = await self.get_user_by_id(user_id)

        if user and user.is_active and user.is_verified and not user.is_deleted:
            # 检查用户email是否匹配
            if user.email != email:
                raise HTTPException(
                    status_code=401,
                    detail=get_message(
                        key="common.insufficientPermissions", lang=language
                    ),
                )

            # 检查是否有有效的refresh token
            statement = (
                select(Token)
                .options(lazyload("*"))
                .where(
                    Token.user_id == user_id,
                    Token.jit == jit,
                    Token.type == TokenType.refresh,
                    Token.is_active == True,
                    Token.expired_at > func.utc_timestamp(),
                )
            )
            result = await self.db.execute(statement)
            refresh_token = result.scalar_one_or_none()

            if not refresh_token:
                raise HTTPException(
                    status_code=404,
                    detail=get_message(
                        key="auth.generateAccessToken.refreshTokenNotFound",
                        lang=language,
                    ),
                )

            # 生成新的access token
            access_jti = str(uuid.uuid4())

            access_token_data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "jti": access_jti,
            }

            access_token, access_token_expired_at = (
                security_manager.create_access_token(access_token_data)
            )

            # 删除旧的access token
            old_access_token_statement = delete(Token).where(
                Token.user_id == user.id, Token.type == TokenType.access
            )
            await self.db.execute(old_access_token_statement)

            # 保存新的access token到数据库
            await self._save_token_to_database(
                user_id=user.id,
                jit=access_jti,
                type=TokenType.access,
                token=access_token,
                expired_at=access_token_expired_at,
            )

            await self.db.commit()

            self.logger.info(
                f"Generated new access token for user: {user.email}")
            return access_token
        else:
            raise HTTPException(
                status_code=401,
                detail=get_message(
                    key="common.insufficientPermissions", lang=language),
            )

    async def social_account_login(
        self,
        request,
        email: str,
        username: str,
        avatar_url: str,
        provider: SocialProvider,
        provider_user_id: str,
        language: Language,
    ) -> Dict[str, str]:
        """Create social account for user"""
        # 查找用户
        user = await self.get_user_by_email(email)
        if user:
            # 检查是否已存在社交账号
            existing_social_account = await self._get_social_account(
                user_id=user.id,
            )
            if (
                existing_social_account
                and existing_social_account.provider.name == provider.name
                and existing_social_account.provider_user_id == provider_user_id
            ):
                # 如果社交账号已存在，用户已绑定, 直接登陆
                self.logger.info(
                    f"Social account already exists for user: {email}, provider: {provider.name}, please direct login."
                )
                # 生成token
                tokens = await self._generate_tokens_by_condition(
                    user_id=user.id,
                    email=user.email,
                    role=user.role,
                    username=user.username,
                )

                access_token = tokens.get("access_token")
                refresh_token = tokens.get("refresh_token")

                # 异步后台任务：更新客户端信息（非阻塞）
                try:
                    if (
                        not user.ip_address
                        or not user.city
                        or not user.latitude
                        or not user.longitude
                    ):
                        # 先发欢迎邮件（延迟10秒），完成后再更新客户端信息
                        task_flow = chain(
                            greeting_email_task.s(user.email, language.value).set(
                                countdown=10
                            ),
                            # 使用 si 确保不接收上一个任务的返回值
                            client_info_task.si(
                                user.id, dict(request.headers)),
                        )
                        task_flow.apply_async()
                        self.logger.info(
                            f"Chained tasks: greeting → client info for {user.email}"
                        )
                    else:
                        # 无需欢迎邮件，直接更新客户端信息（保持10秒延迟以与先前逻辑一致）
                        client_info_task.apply_async(
                            args=[user.id, dict(request.headers)], countdown=10
                        )
                except Exception as e:
                    self.logger.warning(f"启动客户端信息更新任务失败: {e}")

                return {"access_token": access_token, "refresh_token": refresh_token}
            elif existing_social_account and (
                existing_social_account.provider != provider
                or existing_social_account.provider_user_id != provider_user_id
            ):
                # 如果社交账号已存在但是provider不一样, 绑定对应社交账号
                self.logger.info(
                    f"Connect new social {provider.name} account for user: {email}"
                )
                tokens = await self._generate_tokens_by_condition(
                    user_id=user.id,
                    email=user.email,
                    role=user.role,
                    username=user.username,
                )

                access_token = tokens.get("access_token")
                refresh_token = tokens.get("refresh_token")

                # 异步后台任务：更新客户端信息（非阻塞）
                try:
                    if (
                        not user.ip_address
                        or not user.city
                        or not user.latitude
                        or not user.longitude
                    ):
                        # 先发欢迎邮件（延迟10秒），完成后再更新客户端信息
                        task_flow = chain(
                            greeting_email_task.s(user.email, language.value).set(
                                countdown=10
                            ),
                            # 使用 si 确保不接收上一个任务的返回值
                            client_info_task.si(
                                user.id, dict(request.headers)),
                        )
                        task_flow.apply_async()
                        self.logger.info(
                            f"Chained tasks: greeting → client info for {user.email}"
                        )
                    else:
                        # 无需欢迎邮件，直接更新客户端信息（保持10秒延迟以与先前逻辑一致）
                        client_info_task.apply_async(
                            args=[user.id, dict(request.headers)], countdown=10
                        )
                except Exception as e:
                    self.logger.warning(f"启动客户端信息更新任务失败: {e}")

                return {"access_token": access_token, "refresh_token": refresh_token}

        # 如果用户不存在，创建新用户
        user = User(email=email, username=username)
        self.db.add(user)
        await self.db.flush()  # 使用flush而不是commit，保持事务

        # 创建默认头像
        if not avatar_url:
            await self._create_default_avatar(user.id)
        else:
            await self._create_default_avatar(user.id, avatar_url)

        # 更新用户信息
        user.is_verified = True
        user.is_active = True  # 激活用户账户
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 创建社交账号
        social_account = Social_Account(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        self.db.add(social_account)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(social_account)

        tokens = await self._generate_tokens_by_condition(
            user_id=user.id, email=user.email, role=user.role, username=user.username
        )

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        # 添加用户到订阅者列表
        # 使用 ensure_subscriber_active 确保订阅者存在且激活
        subscriber_crud = get_subscriber_crud(self.db)
        await subscriber_crud.ensure_subscriber_active(user.email)

        self.logger.info(
            f"Social account created for user: {email}, provider: {provider}, provider_user_id: {provider_user_id}"
        )

        # 异步后台任务：更新客户端信息（非阻塞）
        try:
            if (
                not user.ip_address
                or not user.city
                or not user.latitude
                or not user.longitude
            ):
                # 先发欢迎邮件（延迟10秒），完成后再更新客户端信息
                task_flow = chain(
                    greeting_email_task.s(
                        user.email, language.value).set(countdown=10),
                    # 使用 si 确保不接收上一个任务的返回值
                    client_info_task.si(user.id, dict(request.headers)),
                )
                task_flow.apply_async()
                self.logger.info(
                    f"Chained tasks: greeting → client info for {user.email}"
                )
            else:
                # 无需欢迎邮件，直接更新客户端信息（保持10秒延迟以与先前逻辑一致）
                client_info_task.apply_async(
                    args=[user.id, dict(request.headers)], countdown=10
                )
        except Exception as e:
            self.logger.warning(f"启动客户端信息更新任务失败: {e}")

        # 清理user list缓存
        await redis_manager.delete_pattern_async("admin_all_users:page=*")

        # 返回访问令牌和刷新令牌
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }


def get_auth_crud(db: AsyncSession = Depends(mysql_manager.get_db)) -> AuthCrud:
    return AuthCrud(db)
