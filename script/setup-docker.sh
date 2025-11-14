#!/bin/bash

set -e

SWAP_SIZE=${SWAP_SIZE:-"2G"}

# 设置 Swap
setup_swap() {
    if [ -f /swapfile ] && swapon --show | grep -q /swapfile; then
        return 0
    fi
    
    if [ -f /swapfile ]; then
        swapoff /swapfile 2>/dev/null || true
        rm -f /swapfile
    fi
    
    sudo fallocate -l ${SWAP_SIZE} /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    fi
}

# 检查 Docker 是否已安装
check_docker_installed() {
    command -v docker &> /dev/null || sudo command -v docker &> /dev/null
}

# 检查 Docker 服务是否正在运行
check_docker_running() {
    sudo systemctl is-active --quiet docker 2>/dev/null || \
    docker ps &> /dev/null 2>&1 || \
    sudo docker ps &> /dev/null 2>&1
}

# 启动 Docker 服务
start_docker() {
    if ! check_docker_running; then
        sudo systemctl start docker
        sleep 2
        if ! check_docker_running; then
            echo "❌ Failed to start Docker service"
            exit 1
        fi
    fi
}

# 清理所有容器
cleanup_containers() {
    DOCKER_CMD="sudo docker"
    if docker ps &> /dev/null 2>&1; then
        DOCKER_CMD="docker"
    fi
    
    $DOCKER_CMD ps -q | xargs -r $DOCKER_CMD stop 2>/dev/null || true
    $DOCKER_CMD ps -aq | xargs -r $DOCKER_CMD rm -f 2>/dev/null || true
}

# 安装 Docker
install_docker() {
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    sudo systemctl start docker
    sudo systemctl enable docker
    
    if [ -n "$SUDO_USER" ]; then
        sudo usermod -aG docker "$SUDO_USER" || true
    else
        sudo usermod -aG docker "$USER" || true
    fi
    
    start_docker
}

# 主流程
setup_swap

if check_docker_installed; then
    start_docker
    cleanup_containers
else
    install_docker
fi
