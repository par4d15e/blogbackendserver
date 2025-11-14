#!/bin/bash

# ========= CONFIG =========
# APP_SERVER_IP: 应用服务器的 IP 地址
# 用于配置 MySQL 用户允许连接的 IP 和防火墙规则
# 这个 IP 是应用服务器的 IP，不是数据库服务器的 IP
APP_SERVER_IP=${APP_SERVER_IP:?"APP_SERVER_IP environment variable is required"}
MYSQL_ROOT_PASS=${MYSQL_ROOT_PASS:?"MYSQL_ROOT_PASS environment variable is required"}
MYSQL_APP_USER=${MYSQL_APP_USER:?"MYSQL_APP_USER environment variable is required"}
MYSQL_APP_PASS=${MYSQL_APP_PASS:?"MYSQL_APP_PASS environment variable is required"}
SWAP_SIZE="2G"
# =========================

echo "📦 Updating System..."
apt update -y && apt upgrade -y

# ========= Check MySQL =========
check_mysql() {
    echo "🔍 Checking MySQL installation and status..."
    
    # Check if MySQL is installed
    if ! command -v mysql &> /dev/null; then
        echo "⚠️  MySQL is not installed"
        return 1
    fi
    
    # Check if MySQL service is running
    if ! systemctl is-active --quiet mysql; then
        echo "⚠️  MySQL service is not running, attempting to start..."
        systemctl start mysql || {
            echo "❌ Failed to start MySQL service"
            return 1
        }
    fi
    
    # Check if MySQL can be connected (try without password first, then with password)
    if mysql -e "SELECT 1;" &> /dev/null; then
        echo "✅ MySQL is installed and accessible (no password required)"
        return 0
    elif mysql -uroot -p${MYSQL_ROOT_PASS} -e "SELECT 1;" &> /dev/null 2>&1; then
        echo "✅ MySQL is installed and accessible with provided password"
        return 0
    else
        echo "⚠️  MySQL is installed but cannot connect"
        return 1
    fi
}

# ========= Manage MySQL App User =========
manage_mysql_app_user() {
    echo "👤 Checking MySQL app user..."
    
    # Get MySQL root connection command
    if mysql -e "SELECT 1;" &> /dev/null; then
        MYSQL_CMD="mysql"
    else
        MYSQL_CMD="mysql -uroot -p${MYSQL_ROOT_PASS}"
    fi
    
    # Check if user exists and get all hosts for this user
    USER_HOSTS=$(${MYSQL_CMD} -sN -e "SELECT Host FROM mysql.user WHERE User='${MYSQL_APP_USER}';" 2>/dev/null)
    
    if [ -z "$USER_HOSTS" ]; then
        # User doesn't exist, create it
        echo "📝 User ${MYSQL_APP_USER} does not exist, creating with host ${APP_SERVER_IP}..."
        ${MYSQL_CMD} -e "CREATE USER '${MYSQL_APP_USER}'@'${APP_SERVER_IP}' IDENTIFIED BY '${MYSQL_APP_PASS}';" 2>/dev/null || {
            echo "❌ Failed to create user ${MYSQL_APP_USER}@${APP_SERVER_IP}"
            return 1
        }
        echo "✅ User ${MYSQL_APP_USER}@${APP_SERVER_IP} created successfully"
    else
        # User exists, check if the desired host exists
        HOST_EXISTS=false
        while IFS= read -r host; do
            if [ "$host" = "${APP_SERVER_IP}" ]; then
                HOST_EXISTS=true
                break
            fi
        done <<< "$USER_HOSTS"
        
        if [ "$HOST_EXISTS" = true ]; then
            # Host matches, just update password and pass
            echo "✅ User ${MYSQL_APP_USER}@${APP_SERVER_IP} already exists, updating password..."
            ${MYSQL_CMD} -e "ALTER USER '${MYSQL_APP_USER}'@'${APP_SERVER_IP}' IDENTIFIED BY '${MYSQL_APP_PASS}';" 2>/dev/null || true
            echo "✅ Password updated for ${MYSQL_APP_USER}@${APP_SERVER_IP}"
        else
            # Host doesn't match, delete all existing hosts and create new one
            echo "⚠️  User ${MYSQL_APP_USER} exists but with different host(s), removing old entries..."
            while IFS= read -r host; do
                echo "   Removing ${MYSQL_APP_USER}@${host}..."
                ${MYSQL_CMD} -e "DROP USER IF EXISTS '${MYSQL_APP_USER}'@'${host}';" 2>/dev/null || true
            done <<< "$USER_HOSTS"
            
            echo "📝 Creating new user ${MYSQL_APP_USER}@${APP_SERVER_IP}..."
            ${MYSQL_CMD} -e "CREATE USER '${MYSQL_APP_USER}'@'${APP_SERVER_IP}' IDENTIFIED BY '${MYSQL_APP_PASS}';" 2>/dev/null || {
                echo "❌ Failed to create user ${MYSQL_APP_USER}@${APP_SERVER_IP}"
                return 1
            }
            echo "✅ User ${MYSQL_APP_USER}@${APP_SERVER_IP} created successfully"
        fi
    fi
    
    # Flush privileges
    ${MYSQL_CMD} -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    return 0
}

MYSQL_NEEDS_INSTALL=true
if check_mysql; then
    echo "✅ MySQL is already installed and working, skipping installation"
    MYSQL_NEEDS_INSTALL=false
else
    echo "🛠 Installing MySQL..."
    apt install -y mysql-server
    
    echo "🔧 Configuring MySQL..."
    mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASS}';" 2>/dev/null || true
    
    # Manage app user (create or update based on host)
    manage_mysql_app_user
    
    # Grant all privileges
    if mysql -e "SELECT 1;" &> /dev/null; then
        mysql -e "GRANT ALL PRIVILEGES ON *.* TO '${MYSQL_APP_USER}'@'${APP_SERVER_IP}'; FLUSH PRIVILEGES;" 2>/dev/null || true
    else
        mysql -uroot -p${MYSQL_ROOT_PASS} -e "GRANT ALL PRIVILEGES ON *.* TO '${MYSQL_APP_USER}'@'${APP_SERVER_IP}'; FLUSH PRIVILEGES;" 2>/dev/null || true
    fi
    
    sed -i "s/bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf
    
    cat <<EOF > /etc/mysql/conf.d/low-memory.cnf
[mysqld]
performance_schema=OFF
innodb_buffer_pool_size=128M
innodb_log_file_size=32M
key_buffer_size=8M
EOF
    
    systemctl restart mysql
    systemctl enable mysql
    
    echo "✅ MySQL Installed & Optimized"
fi

# Create blog database using root user and grant permissions to app user
echo "📚 Creating blog database..."
# Wait a moment for MySQL to be fully ready after restart
sleep 2

# Check if blog database exists, if not create it using root user
if mysql -uroot -p${MYSQL_ROOT_PASS} -e "USE blog;" &> /dev/null 2>&1; then
    echo "✅ Blog database already exists"
else
    echo "📝 Creating blog database..."
    mysql -uroot -p${MYSQL_ROOT_PASS} -e "CREATE DATABASE IF NOT EXISTS blog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
        echo "❌ Failed to create blog database"
        exit 1
    }
    echo "✅ Blog database created successfully"
fi

# Ensure app user exists with correct host before granting permissions
echo "🔐 Ensuring app user is properly configured..."
manage_mysql_app_user

# Grant permissions to app user from APP_SERVER_IP
echo "🔐 Granting permissions to app user..."
if mysql -e "SELECT 1;" &> /dev/null; then
    mysql -e "GRANT ALL PRIVILEGES ON blog.* TO '${MYSQL_APP_USER}'@'${APP_SERVER_IP}'; FLUSH PRIVILEGES;" 2>/dev/null || true
else
    mysql -uroot -p${MYSQL_ROOT_PASS} -e "GRANT ALL PRIVILEGES ON blog.* TO '${MYSQL_APP_USER}'@'${APP_SERVER_IP}'; FLUSH PRIVILEGES;" 2>/dev/null || true
fi
echo "✅ Permissions granted to ${MYSQL_APP_USER}@${APP_SERVER_IP}"

echo "🧠 Checking Swap..."
if [ -f /swapfile ] && swapon --show | grep -q /swapfile; then
    echo "✅ Swap file already exists and is active"
else
    echo "📝 Creating Swap (${SWAP_SIZE})..."
    if [ -f /swapfile ]; then
        echo "⚠️  Swap file exists but not active, removing old file..."
        swapoff /swapfile 2>/dev/null || true
        rm -f /swapfile
    fi
    fallocate -l ${SWAP_SIZE} /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    fi
    echo "✅ Swap Enabled"
fi

# ========= Check Redis =========
check_redis() {
    echo "🔍 Checking Redis installation and status..."
    
    # Check if Redis is installed
    if ! command -v redis-cli &> /dev/null; then
        echo "⚠️  Redis is not installed"
        return 1
    fi
    
    # Check if Redis service is running
    if ! systemctl is-active --quiet redis-server; then
        echo "⚠️  Redis service is not running, attempting to start..."
        systemctl start redis-server || {
            echo "❌ Failed to start Redis service"
            return 1
        }
    fi
    
    # Check if Redis can be connected (no password required)
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is installed and accessible (no password required)"
        return 0
    else
        echo "⚠️  Redis is installed but cannot connect"
        return 1
    fi
}

REDIS_NEEDS_INSTALL=true
if check_redis; then
    echo "✅ Redis is already installed and working, skipping installation"
    REDIS_NEEDS_INSTALL=false
else
    echo "🐳 Installing Redis..."
    apt install -y redis-server
    
    # Remove requirepass if it exists (comment it out or remove it)
    sed -i "s/^requirepass.*/# requirepass (disabled)/" /etc/redis/redis.conf
    sed -i "s/^# requirepass.*/# requirepass (disabled)/" /etc/redis/redis.conf
    sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
    sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf
    
    # Only add memory settings if they don't exist
    if ! grep -q "^maxmemory" /etc/redis/redis.conf; then
        echo "maxmemory 200mb" >> /etc/redis/redis.conf
    fi
    if ! grep -q "^maxmemory-policy" /etc/redis/redis.conf; then
        echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
    fi
    
    systemctl restart redis-server
    systemctl enable redis-server
    
    echo "✅ Redis Installed & Configured"
fi

echo "🛡 Configuring Firewall..."
ufw allow from ${APP_SERVER_IP} to any port 3306
ufw allow from ${APP_SERVER_IP} to any port 6379
ufw allow 22/tcp
ufw --force enable

echo "🎉 DONE!"
echo "==============================="
echo "MySQL Root Password: ${MYSQL_ROOT_PASS}"
echo "MySQL App User: ${MYSQL_APP_USER}"
echo "MySQL App Password: ${MYSQL_APP_PASS}"
echo "App Server Allowed IP: ${APP_SERVER_IP}"
echo "==============================="
echo "🚀 MySQL + Redis Ready!"
