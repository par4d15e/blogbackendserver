"""
Tests for database connection and management.
"""
from unittest.mock import patch


class TestMySQLManager:
    """Tests for MySQL database manager."""

    def test_mysql_manager_initialization(self):
        """Test MySQLManager initialization."""
        with patch('app.core.database.mysql.settings'):
            from app.core.database.mysql import MySQLManager
            manager = MySQLManager()
            
            assert manager.async_engine is None
            assert manager.async_session_maker is None
            assert manager.sync_engine is None
            assert manager.sync_session_maker is None

    def test_get_sqlalchemy_url_mysql(self):
        """Test URL conversion to aiomysql."""
        with patch('app.core.database.mysql.settings') as mock_settings:
            mock_settings.database.DATABASE_URL = "mysql://user:pass@localhost/db"
            
            from app.core.database.mysql import MySQLManager
            manager = MySQLManager()
            url = manager.get_sqlalchemy_url()
            
            assert "mysql+aiomysql://" in url

    def test_get_sqlalchemy_url_pymysql(self):
        """Test URL conversion from pymysql to aiomysql."""
        with patch('app.core.database.mysql.settings') as mock_settings:
            mock_settings.database.DATABASE_URL = "mysql+pymysql://user:pass@localhost/db"
            
            from app.core.database.mysql import MySQLManager
            manager = MySQLManager()
            url = manager.get_sqlalchemy_url()
            
            assert "mysql+aiomysql://" in url

    def test_get_sync_sqlalchemy_url(self):
        """Test sync URL conversion."""
        with patch('app.core.database.mysql.settings') as mock_settings:
            mock_settings.database.DATABASE_URL = "mysql://user:pass@localhost/db"
            
            from app.core.database.mysql import MySQLManager
            manager = MySQLManager()
            url = manager.get_sync_sqlalchemy_url()
            
            assert "mysql+pymysql://" in url


class TestRedisManager:
    """Tests for Redis manager."""

    def test_redis_manager_exists(self):
        """Test RedisManager class exists."""
        from app.core.database.redis import RedisManager
        assert RedisManager is not None

    def test_redis_manager_initialization(self):
        """Test RedisManager initialization."""
        with patch('app.core.database.redis.settings'):
            from app.core.database.redis import RedisManager
            manager = RedisManager()
            
            assert hasattr(manager, 'async_client')
            assert hasattr(manager, 'sync_client')


class TestDatabaseConnection:
    """Tests for database connection manager."""

    def test_db_manager_exists(self):
        """Test database manager exists."""
        from app.core.database.connection import db_manager
        assert db_manager is not None

    def test_db_manager_has_mysql(self):
        """Test db_manager has MySQL manager."""
        from app.core.database.connection import db_manager
        assert hasattr(db_manager, 'mysql_manager')

    def test_db_manager_has_redis(self):
        """Test db_manager has Redis manager."""
        from app.core.database.connection import db_manager
        assert hasattr(db_manager, 'redis_manager')
