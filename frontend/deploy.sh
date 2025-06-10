#!/bin/bash

# 家庭照片视频管理服务 - 前端部署脚本

# 确保脚本在错误时退出
set -e

echo "开始部署前端应用..."

# 安装依赖
echo "安装依赖..."
npm install

# 构建前端
echo "构建前端应用..."
npm run build

# 检查是否要使用Docker部署
if [ "$1" == "--docker" ]; then
    echo "使用Docker部署..."
    docker-compose up -d
    echo "Docker部署完成！访问 http://localhost"
    exit 0
fi

# 检查nginx是否安装
if ! command -v nginx &> /dev/null; then
    echo "Nginx未安装，请安装nginx或使用--docker选项"
    exit 1
fi

# 部署到Nginx
echo "部署到Nginx..."
NGINX_CONF="/etc/nginx/sites-available/family-media-app"
NGINX_ENABLED="/etc/nginx/sites-enabled/family-media-app"

# 检查是否有sudo权限
if [ "$EUID" -ne 0 ]; then
    echo "需要sudo权限配置Nginx..."
    
    # 创建Nginx配置
    sudo cp nginx.conf $NGINX_CONF
    
    # 创建软链接（如果不存在）
    if [ ! -f "$NGINX_ENABLED" ]; then
        sudo ln -s $NGINX_CONF $NGINX_ENABLED
    fi
    
    # 复制构建文件
    sudo mkdir -p /var/www/html
    sudo cp -r dist/* /var/www/html/
    
    # 重启Nginx
    sudo nginx -t && sudo systemctl restart nginx
else
    # 直接配置Nginx
    cp nginx.conf $NGINX_CONF
    
    if [ ! -f "$NGINX_ENABLED" ]; then
        ln -s $NGINX_CONF $NGINX_ENABLED
    fi
    
    mkdir -p /var/www/html
    cp -r dist/* /var/www/html/
    
    nginx -t && systemctl restart nginx
fi

echo "前端部署完成！"
echo "访问 http://localhost 查看应用" 