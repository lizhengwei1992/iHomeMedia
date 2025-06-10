#!/bin/bash

# 简单的前端启动脚本（前后端分离模式）
echo "启动前端服务（前后端分离模式）..."

# 前端目录
cd "$(dirname "$0")"

# 检查dist目录是否存在，如果不存在则构建
if [ ! -d "./dist" ]; then
  echo "构建前端..."
  npm run build
  
  # 检查构建是否成功
  if [ ! -d "./dist" ]; then
    echo "错误：前端构建失败"
    exit 1
  fi
fi

# 使用增强版代理服务器
echo "启动前端服务 (http://localhost:3000)..."
echo "所有API请求将代理到后端 (http://localhost:5000)"

# 使用增强版服务器
python3 server.py

echo "前端服务已停止" 