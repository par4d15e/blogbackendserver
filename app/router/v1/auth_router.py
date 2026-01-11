from fastapi import APIRouter, Depends, Response, Request
from app.services.auth_service import get_auth_service, AuthService
from app.core.logger import logger_manager
from app.core.i18n.i18n import get_message
from app.core.database.dependencies import (
    Dependencies,
    get_access_token_cookie,
    mysql_manager,
)
from app.models.auth_model import CodeType
from app.schemas.common import SuccessResponse
from app.schemas.auth_schemas import (
    SendCodeRequest,
    CreateUserAccountRequest,
    ResetPasswordRequest,
    ResetLoggedInUserPasswordRequest,
    AccountLoginRequest,
)

from app.decorators.rate_limiter import rate_limiter
from app.decorators.email_validator import validate_email_domain

logger = logger_manager.get_logger(__name__)


async def get_current_user_dependency(
    access_token: str = Depends(get_access_token_cookie),
    db=Depends(mysql_manager.get_db),
):
    """Dependency to get current user from tokens"""
    dependencies = Dependencies(db)
    return await dependencies.get_current_user(
        access_token=access_token,
        db=db,
    )


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-verification-code", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
@validate_email_domain()
async def send_verification_code_router(
    request: Request,
    form_data: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.send_auth_code_email(
        email=form_data.email, type=CodeType.verified
    )

    return SuccessResponse(
        message=get_message("auth.sendVerificationCode"),
        data=result,
    )


@router.post("/send-reset-code", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def send_reset_code_router(
    request: Request,
    form_data: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.send_auth_code_email(
        email=form_data.email, type=CodeType.reset
    )

    return SuccessResponse(
        message=get_message("auth.sendResetCode"),
        data=result,
    )


@router.post("/create-user-account", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def create_user_account_router(
    request: Request,
    form_data: CreateUserAccountRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.create_user_account(
        email=form_data.email,
        username=form_data.username,
        password=form_data.password,
        code=form_data.code,
        
    )

    return SuccessResponse(
        message=get_message("auth.createUserAccount"),
        data=result,
    )


@router.post("/reset-user-password", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def reset_user_password_router(
    request: Request,
    form_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.reset_user_password(
        email=form_data.email,
        new_password=form_data.password,
        code=form_data.code,
        
    )

    return SuccessResponse(
        message=get_message("auth.resetUserPassword"),
        data=result,
    )


@router.post("/reset-logged-in-user-password", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def reset_logged_in_user_password_router(
    request: Request,
    form_data: ResetLoggedInUserPasswordRequest,
    current_user=Depends(get_current_user_dependency),
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.reset_logged_in_user_password(
        user_email=current_user.email,
        new_password=form_data.password,
        
    )

    return SuccessResponse(
        message=get_message("auth.resetLoggedInUserPassword"),
        data=result,
    )


@router.post("/account-login", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def account_login_router(
    request: Request,
    form_data: AccountLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.account_login(
        request=request,
        email=form_data.email,
        password=form_data.password,
        response=response,
        
    )
    return SuccessResponse(
        message=get_message("auth.accountLogin.accountLoginSuccess"),
        data=result,
    )


@router.patch("/generate-access-token", response_model=SuccessResponse)
@rate_limiter(limit=5, seconds=60)
async def generate_access_token_router(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.generate_access_token(
        request, response
    )
    return SuccessResponse(
        message=get_message("auth.generateAccessToken.generateAccessTokenSuccess"),
        data=result,
    )


@router.get("/check-auth-token", response_model=SuccessResponse)
async def check_auth_token_router(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.check_auth_token(request)
    return SuccessResponse(
        message=get_message("auth.checkAuthToken"),
        data=result,
    )


@router.get("/github-login")
@rate_limiter(limit=5, seconds=60)
async def github_login_router(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.github_login(request)


@router.get("/github-callback")
async def github_callback_router(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.github_callback(request)


@router.get("/google-login")
@rate_limiter(limit=5, seconds=60)
async def google_login_router(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.google_login(request)


@router.get("/google-callback")
async def google_callback_router(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.google_callback(request)


@router.delete("/account-logout", response_model=SuccessResponse)
@rate_limiter(limit=10, seconds=60)
async def account_logout_router(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user_dependency),
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.account_logout(
        response=response, user_id=current_user.id
    )

    return SuccessResponse(
        message=get_message("auth.accountLogout"),
        data=result,
    )
