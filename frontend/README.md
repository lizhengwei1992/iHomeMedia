# 家庭照片视频管理系统 - 前端

这个项目是家庭照片视频管理系统的前端部分，使用React + TypeScript + Vite开发。

## 技术栈

- React 18
- TypeScript
- Vite
- TailwindCSS
- React Router
- Axios

## 目录结构

```
src/
├── assets/       # 静态资源
├── components/   # 组件
│   ├── auth/     # 认证相关组件
│   ├── layout/   # 布局组件
│   ├── media/    # 媒体相关组件
│   └── ui/       # UI通用组件
├── hooks/        # 自定义钩子
├── pages/        # 页面组件
├── services/     # API服务
├── types/        # TypeScript类型
└── utils/        # 工具函数
```

## 开发

### 前置条件

- Node.js 14+
- npm 或 yarn

### 安装依赖

```bash
npm install
# 或
yarn install
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

开发服务器将在 http://localhost:3000 启动。

## 构建

```bash
npm run build
# 或
yarn build
```

构建产物将输出到 `dist` 目录。

## 部署选项

### 1. 使用部署脚本

我们提供了一个方便的部署脚本，可以自动完成构建和部署步骤：

```bash
# 赋予脚本执行权限
chmod +x deploy.sh

# 使用Nginx部署
./deploy.sh

# 或使用Docker部署
./deploy.sh --docker
```

### 2. 手动部署到Nginx

```bash
# 构建项目
npm run build

# 复制到Nginx目录
sudo cp -r dist/* /var/www/html/

# 复制Nginx配置
sudo cp nginx.conf /etc/nginx/sites-available/family-media-app
sudo ln -s /etc/nginx/sites-available/family-media-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

### 3. 使用Docker部署

```bash
# 使用docker-compose
docker-compose up -d
```

## 与后端集成

前端默认配置中，所有 `/api/*` 请求会被转发到后端服务。

开发模式下，可以在 `vite.config.ts` 中修改代理配置：

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-server',
      changeOrigin: true,
    }
  }
}
```

生产模式下，需要在Nginx配置中设置适当的代理：

```nginx
location /api/ {
    proxy_pass http://backend-server:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
``` 