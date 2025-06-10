# 家庭照片视频管理系统 - 部署指南

本文档提供前端部署的详细指南。

## 环境要求

- Node.js 14+
- Nginx (用于生产环境部署)

## 开发环境

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 构建

```bash
# 构建生产版本
npm run build
```

构建产物将输出到 `dist` 目录。

## 部署方案

### 方案1: Nginx部署（推荐）

1. 构建前端应用
   ```bash
   npm run build
   ```

2. 将构建产物复制到Nginx目录
   ```bash
   cp -r dist/* /var/www/html/
   ```

3. 配置Nginx
   
   创建配置文件：`/etc/nginx/sites-available/family-media-app`
   
   ```nginx
   server {
       listen 80;
       server_name your-domain.com; # 替换为您的域名或IP
       
       root /var/www/html;
       index index.html;
       
       # 所有前端路由重定向到index.html
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       # API请求代理到后端服务
       location /api/ {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # 媒体文件缓存策略
       location ~* \.(jpg|jpeg|png|gif|ico|webp|mp4|mov|avi|heic|hevc)$ {
           expires 7d;
           add_header Cache-Control "public";
       }
       
       # 静态资源缓存策略
       location ~* \.(css|js)$ {
           expires 1d;
           add_header Cache-Control "public";
       }
   }
   ```

4. 启用配置并重启Nginx
   ```bash
   ln -s /etc/nginx/sites-available/family-media-app /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

### 方案2: Docker部署

1. 创建 `Dockerfile`
   
   ```Dockerfile
   # 构建阶段
   FROM node:16-alpine as build
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build
   
   # 生产阶段
   FROM nginx:alpine
   COPY --from=build /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

2. 创建 `nginx.conf`
   
   ```nginx
   server {
       listen 80;
       
       location / {
           root /usr/share/nginx/html;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
       
       location /api/ {
           proxy_pass http://backend:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. 构建并运行Docker镜像
   ```bash
   docker build -t family-media-app-frontend .
   docker run -p 80:80 family-media-app-frontend
   ```

## 环境变量配置

可以通过创建 `.env` 文件来配置环境变量：

```
# .env.production
VITE_API_BASE_URL=http://your-api-url
```

## 注意事项

- 确保后端API服务可访问
- 检查媒体文件的存储路径配置
- 确保文件上传限制已在Nginx配置中调整（默认为1MB）
- 建议使用HTTPS以保证安全性