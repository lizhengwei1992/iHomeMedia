#!/bin/bash

# 家庭媒体应用主启动脚本
echo "=========================================="
echo "  家庭媒体应用启动脚本 - 前后端分离模式"
echo "=========================================="

# 项目根目录
cd "$(dirname "$0")"

# 检查媒体目录权限
echo "检查媒体目录权限..."
MEDIA_DIR="/media"
if [ -d "$MEDIA_DIR" ]; then
  # 获取当前用户
  CURRENT_USER=$(whoami)
  
  # 检查媒体目录所有者
  MEDIA_OWNER=$(ls -ld "$MEDIA_DIR" | awk '{print $3}')
  
  if [ "$MEDIA_OWNER" != "$CURRENT_USER" ]; then
    echo "警告: 媒体目录不属于当前用户，可能导致上传失败"
    echo "尝试修复权限..."
    
    # 尝试修改权限
    chmod -R 777 "$MEDIA_DIR" 2>/dev/null
    
    if [ $? -ne 0 ]; then
      echo "无法修改媒体目录权限，需要管理员权限"
      echo "您可以选择特权模式启动"
    fi
  fi
fi

# 提示用户选择启动模式
echo "请选择启动模式:"
echo "1) 仅启动后端 (http://localhost:5000)"
echo "2) 仅启动前端 (http://localhost:3000)"
echo "3) 同时启动前端和后端 (推荐 - 支持媒体文件代理)"
echo "4) 开发模式：前端代理服务器 + 后端 (支持媒体文件代理)"
echo "5) 纯前端开发模式：Vite热更新 + 后端 (不支持媒体文件预览)"
echo "6) 特权模式：使用sudo权限启动 (解决权限问题)"
read -p "请输入选项 [3]: " choice

# 默认选择3
choice=${choice:-3}

case $choice in
  1)
    echo "仅启动后端..."
    cd backend
    ./start-backend.sh
    ;;
  2)
    echo "仅启动前端..."
    cd frontend
    ./start-frontend.sh
    ;;
  3)
    echo "同时启动前端和后端..."
    
    # 启动后端 (后台运行)
    cd backend
    ./start-backend.sh &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 3
    
    # 启动前端
    cd ../frontend
    ./start-frontend.sh
    
    # 前端停止后，同时停止后端
    echo "正在停止后端服务..."
    kill $BACKEND_PID
    ;;
  4)
    echo "开发模式：前端代理服务器 + 后端 (支持媒体文件代理)..."
    
    # 启动后端 (后台运行)
    cd backend
    ./start-backend.sh &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 3
    
    # 启动前端代理服务器
    cd ../frontend
    echo "启动前端代理服务器 (支持媒体文件访问)..."
    echo "前端服务: http://localhost:3000"
    echo "提示: 修改源代码后请手动运行 'npm run build' 重新构建"
    python server.py
    
    # 前端停止后，同时停止后端
    echo "正在停止后端服务..."
    kill $BACKEND_PID
    ;;
  5)
    echo "纯前端开发模式：Vite热更新 + 后端 (不支持媒体文件预览)..."
    
    # 启动后端 (后台运行)
    cd backend
    ./start-backend.sh &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 3
    
    # 启动前端开发服务器
    cd ../frontend
    echo "启动Vite开发服务器..."
    echo "注意: 此模式不支持媒体文件预览，仅用于前端代码开发"
    npm run dev
    
    # 前端停止后，同时停止后端
    echo "正在停止后端服务..."
    kill $BACKEND_PID
    ;;
  6)
    echo "特权模式：使用sudo权限启动..."
    echo "修复媒体目录权限..."
    
    # 修复权限
    sudo chown -R $USER:$USER "$MEDIA_DIR"
    sudo chmod -R 755 "$MEDIA_DIR"
    sudo mkdir -p "$MEDIA_DIR/photos" "$MEDIA_DIR/videos" "$MEDIA_DIR/thumbnails"
    
    echo "权限修复完成，以普通模式启动..."
    
    # 启动后端 (后台运行)
    cd backend
    ./start-backend.sh &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 3
    
    # 启动前端
    cd ../frontend
    ./start-frontend.sh
    
    # 前端停止后，同时停止后端
    echo "正在停止后端服务..."
    kill $BACKEND_PID
    ;;
  *)
    echo "无效选项: $choice"
    exit 1
    ;;
esac

echo "应用已停止"