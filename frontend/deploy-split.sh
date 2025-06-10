#!/bin/bash

# 前后端分离部署脚本
echo "前后端分离部署脚本启动..."

# 前端构建
echo "1. 构建前端..."
cd "$(dirname "$0")"
npm run build

# 确认构建成功
if [ ! -d "./dist" ]; then
  echo "错误: 前端构建失败，dist目录不存在"
  exit 1
fi

# 检查是否安装了nginx
if ! command -v nginx &> /dev/null; then
  echo "警告: 系统未安装nginx，将使用Python提供静态文件服务"
  
  # 使用Python提供静态文件服务
  echo "使用Python HTTP服务提供前端文件 (端口3000)"
  cd dist
  python3 -m http.server 3000 &
  FRONTEND_PID=$!
  echo "前端服务进程ID: $FRONTEND_PID"
  echo "前端地址: http://localhost:3000"
  
  echo "请确保后端服务运行在 http://localhost:5000"
  echo "前端已配置将API请求代理到后端"
  
  # 保存进程ID以便稍后清理
  echo $FRONTEND_PID > .frontend.pid
  
  echo "使用Ctrl+C停止服务"
  wait $FRONTEND_PID
else
  # 使用Nginx部署
  echo "2. 配置Nginx..."
  
  # 创建Nginx配置
  NGINX_CONF_DIR="/etc/nginx/conf.d"
  NGINX_CONF_FILE="$NGINX_CONF_DIR/family-media-app.conf"
  
  # 检查是否有写入权限
  if [ ! -w "$NGINX_CONF_DIR" ]; then
    echo "警告: 无权写入Nginx配置目录，将创建本地配置"
    NGINX_CONF_FILE="./nginx.local.conf"
    
    # 创建本地Nginx配置
    cat > $NGINX_CONF_FILE << EOF
server {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    location / {
        root $(pwd)/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
    
    echo "创建了本地Nginx配置: $NGINX_CONF_FILE"
    echo "请手动将此配置复制到Nginx配置目录"
    echo "然后重启Nginx: sudo systemctl restart nginx"
  else
    # 直接写入Nginx配置
    sudo tee $NGINX_CONF_FILE > /dev/null << EOF
server {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    location / {
        root $(pwd)/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
    
    # 重启Nginx
    echo "3. 重启Nginx..."
    sudo systemctl restart nginx
    
    if [ $? -eq 0 ]; then
      echo "Nginx重启成功"
      echo "前端部署完成: http://localhost"
      echo "确保后端服务运行在 http://localhost:5000"
    else
      echo "Nginx重启失败，请手动重启"
    fi
  fi
fi 