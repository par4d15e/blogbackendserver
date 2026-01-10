"""
Tests for API routes (integration tests).
"""
import pytest


class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_docs_endpoint_accessible(self):
        """Test that docs endpoint configuration exists."""
        # This tests that the router is properly configured
        from app.router.v1 import docs_router
        assert docs_router is not None


class TestAuthRoutes:
    """Tests for authentication routes."""

    @pytest.fixture
    def auth_router(self):
        """Get auth router."""
        from app.router.v1.auth_router import router
        return router

    def test_auth_router_has_routes(self, auth_router):
        """Test that auth router has expected routes."""
        routes = [route.path for route in auth_router.routes]

        assert "/auth/send-verification-code" in routes
        assert "/auth/send-reset-code" in routes
        assert "/auth/create-user-account" in routes
        assert "/auth/reset-user-password" in routes

    def test_auth_router_prefix(self, auth_router):
        """Test auth router has correct prefix."""
        assert auth_router.prefix == "/auth"


class TestBlogRoutes:
    """Tests for blog routes."""

    @pytest.fixture
    def blog_router(self):
        """Get blog router."""
        from app.router.v1.blog_router import router
        return router

    def test_blog_router_exists(self, blog_router):
        """Test that blog router exists."""
        assert blog_router is not None
        assert blog_router.prefix == "/blog"


class TestUserRoutes:
    """Tests for user routes."""

    @pytest.fixture
    def user_router(self):
        """Get user router."""
        from app.router.v1.user_router import router
        return router

    def test_user_router_exists(self, user_router):
        """Test that user router exists."""
        assert user_router is not None
        assert user_router.prefix == "/user"


class TestPaymentRoutes:
    """Tests for payment routes."""

    @pytest.fixture
    def payment_router(self):
        """Get payment router."""
        from app.router.v1.payment_router import router
        return router

    def test_payment_router_exists(self, payment_router):
        """Test that payment router exists."""
        assert payment_router is not None
        assert payment_router.prefix == "/payment"


class TestMediaRoutes:
    """Tests for media routes."""

    @pytest.fixture
    def media_router(self):
        """Get media router."""
        from app.router.v1.media_router import router
        return router

    def test_media_router_exists(self, media_router):
        """Test that media router exists."""
        assert media_router is not None
        assert media_router.prefix == "/media"


class TestProjectRoutes:
    """Tests for project routes."""

    @pytest.fixture
    def project_router(self):
        """Get project router."""
        from app.router.v1.project_router import router
        return router

    def test_project_router_exists(self, project_router):
        """Test that project router exists."""
        assert project_router is not None
        assert project_router.prefix == "/project"


class TestSeoRoutes:
    """Tests for SEO routes."""

    @pytest.fixture
    def seo_router(self):
        """Get seo router."""
        from app.router.v1.seo_router import router
        return router

    def test_seo_router_exists(self, seo_router):
        """Test that seo router exists."""
        assert seo_router is not None
        assert seo_router.prefix == "/seo"


class TestTagRoutes:
    """Tests for tag routes."""

    @pytest.fixture
    def tag_router(self):
        """Get tag router."""
        from app.router.v1.tag_router import router
        return router

    def test_tag_router_exists(self, tag_router):
        """Test that tag router exists."""
        assert tag_router is not None
        assert tag_router.prefix == "/tag"


class TestFriendRoutes:
    """Tests for friend routes."""

    @pytest.fixture
    def friend_router(self):
        """Get friend router."""
        from app.router.v1.friend_router import router
        return router

    def test_friend_router_exists(self, friend_router):
        """Test that friend router exists."""
        assert friend_router is not None
        assert friend_router.prefix == "/friend"


class TestSubscriberRoutes:
    """Tests for subscriber routes."""

    @pytest.fixture
    def subscriber_router(self):
        """Get subscriber router."""
        from app.router.v1.subscriber_router import router
        return router

    def test_subscriber_router_exists(self, subscriber_router):
        """Test that subscriber router exists."""
        assert subscriber_router is not None
        assert subscriber_router.prefix == "/subscriber"


class TestBoardRoutes:
    """Tests for board routes."""

    @pytest.fixture
    def board_router(self):
        """Get board router."""
        from app.router.v1.board_router import router
        return router

    def test_board_router_exists(self, board_router):
        """Test that board router exists."""
        assert board_router is not None
        assert board_router.prefix == "/board"


class TestSectionRoutes:
    """Tests for section routes."""

    @pytest.fixture
    def section_router(self):
        """Get section router."""
        from app.router.v1.section_router import router
        return router

    def test_section_router_exists(self, section_router):
        """Test that section router exists."""
        assert section_router is not None
        assert section_router.prefix == "/section"


class TestAnalyticRoutes:
    """Tests for analytic routes."""

    @pytest.fixture
    def analytic_router(self):
        """Get analytic router."""
        from app.router.v1.analytic_router import router
        return router

    def test_analytic_router_exists(self, analytic_router):
        """Test that analytic router exists."""
        assert analytic_router is not None
        assert analytic_router.prefix == "/analytic"
