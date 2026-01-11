import os
from contextlib import asynccontextmanager
from typing import Any, cast
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware import Middleware
from fastapi.staticfiles import StaticFiles


from app.core.i18n.i18n import get_message, set_request_language, get_language
from app.core.logger import logger_manager
from app.core.database.connection import db_manager
from app.core.config.settings import settings
from app.schemas.common import SuccessResponse
from app.router.v1 import (
    auth_router,
    user_router,
    blog_router,
    section_router,
    seo_router,
    tag_router,
    board_router,
    friend_router,
    media_router,
    docs_router,
    payment_router,
    project_router,
    analytic_router,
    subscriber_router,
)


# 创建LoggerManager实例
logger_manager.setup()


# 创建Logger实例
logger = logger_manager.get_logger(__name__)


# CORS中间件配置
allow_origins = [
    x.strip() for x in settings.cors.CORS_ALLOWED_ORIGINS.split(",") if x.strip()
]
allow_methods = [
    x.strip() for x in settings.cors.CORS_ALLOW_METHODS.split(",") if x.strip()
]
allow_headers = [
    x.strip() for x in settings.cors.CORS_ALLOW_HEADERS.split(",") if x.strip()
]
allow_credentials = settings.cors.CORS_ALLOW_CREDENTIALS
expose_headers = [
    x.strip() for x in settings.cors.CORS_EXPOSE_HEADERS.split(",") if x.strip()
]

# Session中间件配置
session_secret_key = settings.csrf.CSRF_SECRET_KEY.get_secret_value()

# 中间件列表（使用 Middleware 类实现类型安全）
middleware = [
    Middleware(
        cast(Any, SessionMiddleware),
        secret_key=session_secret_key,
        https_only=True,
        same_site="lax",
    ),
    Middleware(
        cast(Any, CORSMiddleware),
        allow_origins=allow_origins,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        allow_credentials=allow_credentials,
        expose_headers=expose_headers,
    ),
]


# 创建生命周期
@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("🚩 Starting the application...")
    logger.info(f"🚧 You are Working in {os.getenv('ENV')} Environment")

    try:
        # 初始化数据库连接
        await db_manager.initialize()
        logger.info("🎉 Database connections initialized successfully")
        await db_manager.test_connections()
        logger.info("🎉 Database connections test successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning(
            "⚠️ Application will start without database connections")

    yield

    # 关闭数据库连接
    try:
        await db_manager.close()
        logger.info("🎉 Database connections closed successfully")
    except Exception as e:
        logger.error(f"❌ Database connection closed failed: {e}")
        logger.warning("⚠️ Database connection closed failed")


# 创建FastAPI实例
app = FastAPI(
    lifespan=lifespan,
    title=settings.app.APP_NAME,
    middleware=middleware,
    docs_url=None,  # 禁用默认 docs，使用自定义
    redoc_url=None,  # 禁用默认 redoc，使用自定义
)


# 语言检测中间件（必须在其他中间件之后注册）
@app.middleware("http")
async def language_middleware(request: Request, call_next):
    """自动检测并设置请求语言到上下文"""
    language = get_language(request)
    set_request_language(language)
    response = await call_next(request)
    return response


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc}")
    error_detail = exc.detail

    if isinstance(error_detail, dict):
        # 如果detail是字典，直接使用error字段
        error_message = error_detail.get("error", str(error_detail))
    else:
        # 如果detail是字符串，直接使用
        error_message = str(error_detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "error": error_message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    logger.error(f"Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "error": get_message("common.internalError"),
        },
    )


# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


# 根路径健康检查
@app.get("/", tags=["Health"], response_model=SuccessResponse)
async def root():
    return SuccessResponse(
        message=get_message("common.serverRunning"),
        data=None,
    )


# Favicon 处理
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = "static/image/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    return JSONResponse(content={}, status_code=204)


# 自定义 Swagger UI（使用自定义 favicon）
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.app.APP_NAME} - Swagger UI",
        swagger_favicon_url="/static/image/favicon.ico?v=2",
    )


# 自定义 ReDoc（使用自定义 favicon）
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.app.APP_NAME} - ReDoc",
        redoc_favicon_url="/static/image/favicon.ico?v=2",
    )


# 注册路由
app.include_router(docs_router.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(user_router.router, prefix="/api/v1")
app.include_router(section_router.router, prefix="/api/v1")
app.include_router(blog_router.router, prefix="/api/v1")
app.include_router(board_router.router, prefix="/api/v1")
app.include_router(friend_router.router, prefix="/api/v1")
app.include_router(seo_router.router, prefix="/api/v1")
app.include_router(tag_router.router, prefix="/api/v1")
app.include_router(media_router.router, prefix="/api/v1")
app.include_router(payment_router.router, prefix="/api/v1")
app.include_router(project_router.router, prefix="/api/v1")
app.include_router(analytic_router.router, prefix="/api/v1")
app.include_router(subscriber_router.router, prefix="/api/v1")


# OpenAPI 文档配置
def custom_openapi(self: FastAPI) -> dict[str, Any]:
    if self.openapi_schema:
        return self.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app.APP_NAME,
        version=settings.app.APP_VERSION,
        description=settings.app.APP_DESCRIPTION,
        routes=self.routes,
        terms_of_service="https://heyxiaoli.com/copyright",
        contact={
            "name": "ning3739",
            "url": "https://heyxiaoli.com",
            "email": "ln729500172@gmail.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://github.com/ning3739/blogbackendserver?tab=MIT-1-ov-file",
        },
    )

    # 添加 Logo
    openapi_schema["info"]["x-logo"] = {
        "url": "https://github.com/ning3739/blogbackendserver/blob/main/static/image/logo.png?raw=true",
        "altText": settings.app.APP_NAME,
    }

    # 自定义标签描述和排序（名称必须与路由中定义的完全匹配）
    openapi_schema["tags"] = [
        {"name": "Health", "description": "Health check endpoints"},
        {"name": "Documentation", "description": "API documentation endpoints"},
        {"name": "Authentication", "description": "User authentication and authorization"},
        {"name": "User", "description": "User profile and account management"},
        {"name": "Blog", "description": "Blog post CRUD operations"},
        {"name": "Section", "description": "Blog sections and categories"},
        {"name": "Tag", "description": "Tag management for blog posts"},
        {"name": "Media", "description": "Media file upload and management"},
        {"name": "Board", "description": "Message board operations"},
        {"name": "Friend", "description": "Friend links management"},
        {"name": "Project", "description": "Project portfolio showcase"},
        {"name": "Payment", "description": "Stripe payment processing"},
        {"name": "Seo", "description": "SEO metadata configuration"},
        {"name": "Analytic", "description": "Analytics and statistics data"},
        {"name": "Subscriber", "description": "Newsletter subscriber management"},
    ]

    self.openapi_schema = openapi_schema
    return self.openapi_schema


object.__setattr__(app, "openapi", custom_openapi.__get__(app, type(app)))


# 启动FastAPI应用
# if os.getenv("ENV") == "development":
if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        logger.info("🚩 Starting the application in development mode...")

        uvicorn.run(
            app="app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            ssl_keyfile="certs/localhost-key.pem",
            ssl_certfile="certs/localhost.pem",
        )
