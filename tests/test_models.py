"""
Tests for SQLModel models.
"""


class TestUserModel:
    """Tests for User model."""

    def test_user_model_fields(self):
        """Test User model has expected fields."""
        from app.models.user_model import User
        
        # Check model has expected attributes
        assert hasattr(User, 'id')
        assert hasattr(User, 'email')
        assert hasattr(User, 'username')
        assert hasattr(User, 'is_active')
        assert hasattr(User, 'is_verified')
        assert hasattr(User, 'is_deleted')
        assert hasattr(User, 'created_at')
        assert hasattr(User, 'updated_at')

    def test_role_type_enum(self):
        """Test RoleType enum values."""
        from app.models.user_model import RoleType
        
        assert RoleType.user == 1
        assert RoleType.admin == 2


class TestBlogModel:
    """Tests for Blog model."""

    def test_blog_model_fields(self):
        """Test Blog model has expected fields."""
        from app.models.blog_model import Blog
        
        assert hasattr(Blog, 'id')
        assert hasattr(Blog, 'chinese_title')
        assert hasattr(Blog, 'slug')
        assert hasattr(Blog, 'chinese_content')
        assert hasattr(Blog, 'user_id')


class TestAuthModel:
    """Tests for Auth models."""

    def test_code_type_enum(self):
        """Test CodeType enum values."""
        from app.models.auth_model import CodeType
        
        assert hasattr(CodeType, 'verified')
        assert hasattr(CodeType, 'reset')

    def test_social_provider_enum(self):
        """Test SocialProvider enum."""
        from app.models.auth_model import SocialProvider
        
        assert hasattr(SocialProvider, 'github')
        assert hasattr(SocialProvider, 'google')


class TestPaymentModel:
    """Tests for Payment models."""

    def test_payment_record_model_fields(self):
        """Test Payment_Record model has expected fields."""
        from app.models.payment_model import Payment_Record
        
        assert hasattr(Payment_Record, 'id')
        assert hasattr(Payment_Record, 'user_id')
        assert hasattr(Payment_Record, 'amount')


class TestMediaModel:
    """Tests for Media model."""

    def test_media_model_fields(self):
        """Test Media model has expected fields."""
        from app.models.media_model import Media
        
        assert hasattr(Media, 'id')
        assert hasattr(Media, 'user_id')
        assert hasattr(Media, 'uuid')


class TestTagModel:
    """Tests for Tag model."""

    def test_tag_model_fields(self):
        """Test Tag model has expected fields."""
        from app.models.tag_model import Tag
        
        assert hasattr(Tag, 'id')
        assert hasattr(Tag, 'chinese_title')
        assert hasattr(Tag, 'slug')


class TestProjectModel:
    """Tests for Project model."""

    def test_project_model_fields(self):
        """Test Project model has expected fields."""
        from app.models.project_model import Project
        
        assert hasattr(Project, 'id')
        assert hasattr(Project, 'chinese_title')


class TestSeoModel:
    """Tests for SEO model."""

    def test_seo_model_fields(self):
        """Test SEO model has expected fields."""
        from app.models.seo_model import Seo
        
        assert hasattr(Seo, 'id')
        assert hasattr(Seo, 'chinese_title')


class TestFriendModel:
    """Tests for Friend model."""

    def test_friend_model_fields(self):
        """Test Friend model has expected fields."""
        from app.models.friend_model import Friend
        
        assert hasattr(Friend, 'id')


class TestSubscriberModel:
    """Tests for Subscriber model."""

    def test_subscriber_model_fields(self):
        """Test Subscriber model has expected fields."""
        from app.models.subscriber_model import Subscriber
        
        assert hasattr(Subscriber, 'id')
        assert hasattr(Subscriber, 'email')


class TestBoardModel:
    """Tests for Board model."""

    def test_board_model_fields(self):
        """Test Board model has expected fields."""
        from app.models.board_model import Board
        
        assert hasattr(Board, 'id')


class TestSectionModel:
    """Tests for Section model."""

    def test_section_model_fields(self):
        """Test Section model has expected fields."""
        from app.models.section_model import Section
        
        assert hasattr(Section, 'id')
