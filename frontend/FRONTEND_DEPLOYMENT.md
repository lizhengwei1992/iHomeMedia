# 前后端分离部署指南

## 概述

本文档介绍如何在前后端分离模式下部署家庭媒体应用。前后端分离部署意味着前端和后端可以独立运行和部署，通过API接口通信。

## 部署选项

有以下几种方式可以部署前端：

### 1. 使用Python HTTP服务器（简单方式）

适用于简单测试和临时部署：

```bash
# 前端目录
cd frontend

# 构建前端
npm run build

# 使用Python启动HTTP服务器（端口3000）
cd dist
python3 -m http.server 3000
```

访问 http://localhost:3000 即可查看前端应用

### 2. 使用CORS增强的Python服务器（开发模式）

我们提供了一个支持CORS和SPA路由的增强版Python服务器：

```bash
# 前端目录
cd frontend

# 构建前端
npm run build

# 启动增强版服务器
python3 server.py
```

### 3. 使用Nginx（推荐生产环境）

Nginx配置示例 (`/etc/nginx/conf.d/family-media-app.conf`):

```nginx
server {
    listen 80;
    server_name localhost;  # 或您的域名
    
    # 前端静态文件
    location / {
        root /home/lzw/app/family_media_app/frontend/dist;  # 更改为您的dist目录路径
        index index.html;
        try_files $uri $uri/ /index.html;  # 支持SPA路由
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000;  # 后端地址
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

重启Nginx: `sudo systemctl restart nginx`

## 前端API配置

前端配置了API请求代理，确保在开发和生产环境中都能正确访问后端API：

1. **开发环境**: 
   - `vite.config.ts` 中配置了代理，将 `/api` 请求转发到后端
   - 确保API基础路径设置为 `/api/v1`

2. **生产环境**: 
   - 通过Nginx配置，将 `/api` 请求代理到后端服务

## 后端配置

后端需要：

1. 确保CORS配置正确：
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 生产环境应限制为具体域名
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. 启动后端服务：
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
   ```

## 前后端通信

- 前端API服务配置在 `frontend/src/services/api.ts`
- 已配置baseURL为 `/api/v1` 以匹配后端API路径
- 确保所有API路径与后端路由匹配

## 常见问题排查

1. **前端显示API错误**:
   - 检查后端是否正在运行
   - 验证API基础路径是否正确
   - 查看浏览器控制台网络请求是否返回CORS错误

2. **路由问题**:
   - 确保Nginx配置中包含 `try_files $uri $uri/ /index.html;`
   - SPA应用需要将所有前端路由请求转发到index.html

3. **API请求404**:
   - 确认API路径是否包含正确版本前缀 `/api/v1`
   - 检查后端API路由是否注册正确 