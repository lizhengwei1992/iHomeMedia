#!/bin/bash

# 后端启动脚本
echo "启动后端服务..."

# 后端目录
cd "$(dirname "$0")"

# 检查是否安装了所需的依赖
echo "检查环境..."
if ! command -v uvicorn &> /dev/null; then
  echo "警告: uvicorn未安装，尝试安装..."
  pip install uvicorn fastapi
fi

# 检查媒体目录权限
MEDIA_DIR="/media"
if [ -d "$MEDIA_DIR" ]; then
  echo "检查媒体目录权限..."
  
  # 获取当前用户
  CURRENT_USER=$(whoami)
  
  # 检查媒体目录所有者
  MEDIA_OWNER=$(ls -ld "$MEDIA_DIR" | awk '{print $3}')
  
  if [ "$MEDIA_OWNER" != "$CURRENT_USER" ]; then
    echo "警告: 媒体目录($MEDIA_DIR)不属于当前用户($CURRENT_USER)，可能导致上传失败"
    echo "尝试修复权限..."
    
    # 尝试修改权限
    chmod -R 777 "$MEDIA_DIR" 2>/dev/null
    
    if [ $? -eq 0 ]; then
      echo "已设置媒体目录为全局可写"
    else
      echo "无法修改媒体目录权限，请使用以下命令手动修复:"
      echo "sudo chown -R $CURRENT_USER:$CURRENT_USER $MEDIA_DIR"
      echo "或者"
      echo "sudo chmod -R 777 $MEDIA_DIR"
    fi
  fi
  
  # 确保子目录存在且有写入权限
  mkdir -p "$MEDIA_DIR/photos" "$MEDIA_DIR/videos" "$MEDIA_DIR/thumbnails"
  chmod -R 777 "$MEDIA_DIR/photos" "$MEDIA_DIR/videos" "$MEDIA_DIR/thumbnails" 2>/dev/null
fi

# 设置媒体目录环境变量
export MEDIA_DIR="/media"

# 启动后端服务
echo "启动后端API服务 (http://localhost:5000)..."
echo "媒体目录设置为: $MEDIA_DIR"
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

echo "后端服务已停止" 