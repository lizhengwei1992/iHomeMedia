#!/bin/bash

# 家庭照片视频管理服务 - 前端简易部署脚本

# 确保脚本在错误时退出
set -e

echo "开始部署前端应用..."

# 安装依赖
echo "安装依赖..."
npm install

# 构建前端
echo "构建前端应用..."
npm run build

# 根据参数执行不同的部署方式
if [ "$1" == "--docker" ]; then
    echo "使用Docker部署..."
    
    # 检查docker是否安装
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        echo "Error: 需要安装 docker 和 docker-compose"
        exit 1
    fi
    
    # 启动docker容器
    docker-compose up -d
    echo "Docker部署完成！访问 http://localhost"
    exit 0
fi

# 简易静态服务器（使用 Python）
if command -v python3 &> /dev/null; then
    echo "使用 Python 简易服务器部署..."
    echo "启动服务器在端口 8080..."
    echo "可以通过 Ctrl+C 停止服务器"
    echo "访问 http://localhost:8080 查看应用"
    
    cd dist && python3 -m http.server 8080
    exit 0
elif command -v python &> /dev/null; then
    echo "使用 Python 简易服务器部署..."
    echo "启动服务器在端口 8080..."
    echo "可以通过 Ctrl+C 停止服务器"
    echo "访问 http://localhost:8080 查看应用"
    
    cd dist && python -m SimpleHTTPServer 8080
    exit 0
else
    echo "Error: 未找到 Python 或 Docker，无法启动简易服务器"
    echo "您可以："
    echo "  1. 安装 Python 3 或 Docker"
    echo "  2. 手动将 dist 目录中的文件复制到您的 Web 服务器目录"
    exit 1
fi 