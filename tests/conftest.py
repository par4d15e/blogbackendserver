"""
Pytest configuration and fixtures for the test suite.
"""
import os
import asyncio
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment before importing app modules
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "mysql+aiomysql://test:test@localhost:3306/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["CSRF_SECRET_KEY"] = "test-csrf-secret-key"
os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_S3_BUCKET_NAME"] = "test-bucket"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000"
os.environ["CORS_ALLOW_METHODS"] = "GET,POST,PUT,DELETE"
os.environ["CORS_ALLOW_HEADERS"] = "*"
os.environ["CORS_ALLOW_CREDENTIALS"] = "true"
os.environ["CORS_EXPOSE_HEADERS"] = ""
os.environ["GITHUB_CLIENT_ID"] = "test-github-id"
os.environ["GITHUB_CLIENT_SECRET"] = "test-github-secret"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-secret"
os.environ["GITHUB_REDIRECT_URI"] = "https://example.com/github/callback"
os.environ["GOOGLE_REDIRECT_URI"] = "https://example.com/google/callback"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_xxx"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_xxx"
os.environ["QWEN_API_KEY"] = "test-qwen-key"
os.environ["AZURE_SPEECH_KEY"] = "test-azure-key"
os.environ["AZURE_SPEECH_REGION"] = "eastus"
os.environ["EMAIL_HOST"] = "smtp.test.com"
os.environ["EMAIL_PORT"] = "587"
os.environ["EMAIL_HOST_USER"] = "test@test.com"
os.environ["EMAIL_HOST_PASSWORD"] = "test-password"
os.environ["EMAIL_USERNAME"] = "test@test.com"
os.environ["EMAIL_PASSWORD"] = "test-password"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"
os.environ["STRIPE_PUBLIC_KEY"] = "pk_test_xxx"
os.environ["SUCCESS_URL"] = "https://example.com/success"
os.environ["CANCEL_URL"] = "https://example.com/cancel"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.expire = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "$argon2id$v=19$m=65536,t=2,p=1$xxx",
        "is_active": True,
        "is_verified": True,
        "is_deleted": False,
        "role": 1,
    }


@pytest.fixture
def sample_blog_data() -> dict:
    """Sample blog data for testing."""
    return {
        "id": 1,
        "title": "Test Blog Post",
        "slug": "test-blog-post",
        "content": "This is test content.",
        "author_id": 1,
        "is_published": True,
    }


@pytest.fixture
def auth_headers() -> dict:
    """Sample auth headers for testing."""
    return {
        "Authorization": "Bearer test-access-token",
        "Cookie": "access_token=test-access-token; refresh_token=test-refresh-token",
    }
