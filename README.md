# 家庭照片视频管理服务

基于 FastAPI 和 React 构建的家庭照片视频管理系统，支持在本地 Linux 主机上搭建一套可以通过手机浏览器访问的照片和视频管理服务。

## 功能特点

### 📱 媒体文件管理
- 手机端（Safari 浏览器）批量上传照片/视频
- 浏览已上传的照片/视频库，支持分页和筛选
- 文件存储于 Linux 主机本地磁盘
- 所有上传的照片/视频保留原始质量
- 支持 Apple 格式文件（HEIC、MOV 等）
- 自动生成缩略图，优化浏览体验

### 🔍 智能搜索功能
- **文本搜索**: 根据图片内容描述进行搜索
- **以图搜图**: 上传图片查找相似内容
- **找相似**: 基于现有照片查找相似图片
- **多模态搜索**: 同时支持文本和图像的混合搜索
- AI驱动的内容理解和相似性匹配

### 🤖 AI增强特性
- 自动生成图片内容描述
- 智能向量化存储（基于阿里云DashScope）
- 支持自定义描述和标签管理
- 后台异步处理，不阻塞用户操作

### 🔐 安全与认证
- 提供基础身份认证（单一账户密码登录）
- 支持JWT token安全认证
- 设计为家庭局域网内安全使用

## 系统要求

### 基础环境
- **操作系统**: Linux（Ubuntu 20.04+ 推荐）
- **Docker**: 20.10.0+ 
- **Docker Compose**: 1.29.0+
- **存储空间**: 建议至少50GB可用空间（用于媒体文件存储）
- **内存**: 建议4GB+（运行容器和AI服务）

### 网络环境
- 局域网环境
- 互联网连接（用于AI功能访问阿里云DashScope）

### API服务
- **阿里云DashScope API密钥**（用于AI功能，必需）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/lizhengwei1992/iHomeMedia.git
cd iHomeMedia
```

### 2. 准备媒体存储目录

确保主机上的 `/media` 目录存在且有适当权限：

```bash
sudo mkdir -p /media/{photos,videos,thumbnails,qdrant}
sudo chmod -R 755 /media
```

### 3. 配置环境变量

复制环境变量模板并配置：

```bash
cp env.template .local.env
```

编辑 `.local.env` 文件，配置必要的环境变量：

```bash
# 阿里云DashScope API密钥（必需）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 用户认证信息
USERNAME=family
PASSWORD=123456

# Qdrant数据库配置（使用独立部署）
QDRANT_URL=http://host.docker.internal:6333

# 其他配置项根据需要调整
SECRET_KEY=your-secret-key-here
```

### 4. 部署方式选择

根据不同需求，提供两种部署方式：

#### 方式一：完整Docker部署（推荐）

使用部署脚本自动化部署：

```bash
chmod +x deploy.sh
./deploy.sh
```

部署脚本采用混合架构：
- ✅ 独立部署Qdrant向量数据库
- ✅ Docker Compose部署前后端服务
- ✅ 自动处理网络连接和健康检查
- ✅ 支持向量维度自动修复

#### 方式二：前后端分离部署

适合开发调试或资源有限环境：

```bash
# 1. 首先单独启动Qdrant数据库
docker run -d --name qdrant-standalone \
  --restart unless-stopped \
  -p 6333:6333 \
  -v /media/qdrant:/qdrant/storage \
  qdrant/qdrant:latest

# 2. 使用前后端分离脚本启动应用
chmod +x start-app.sh
./start-app.sh
```

### 5. 访问应用

部署成功后，通过以下地址访问：

- **前端应用**: http://localhost:3000
- **API文档**: http://localhost:3000/api/v1/docs
- **Qdrant仪表板**: http://localhost:6333/dashboard

## 服务管理

### 完整Docker部署管理

```bash
# 查看所有服务状态
docker-compose ps
docker ps --filter "name=qdrant-standalone"

# 查看日志
docker-compose logs -f              # 前后端日志
docker logs -f qdrant-standalone    # Qdrant日志

# 停止服务
docker-compose down                 # 停止前后端
docker stop qdrant-standalone       # 停止Qdrant

# 停止所有服务
docker-compose down && docker stop qdrant-standalone

# 重启服务
docker-compose restart              # 重启前后端
docker restart qdrant-standalone    # 重启Qdrant

# 完全重新构建部署
./deploy.sh --build    # 强制重建
./deploy.sh --clean    # 清理旧数据后重建
```

### 前后端分离部署管理

```bash
# 启动应用（选择启动模式：仅后端/仅前端/同时启动）
./start-app.sh

# 停止应用（提供多种停止选项）
./stop-app.sh

# 管理Qdrant数据库
docker stop qdrant-standalone     # 停止
docker start qdrant-standalone    # 重启
docker logs -f qdrant-standalone  # 查看日志
```

### Deploy脚本选项

```bash
./deploy.sh                    # 正常部署
./deploy.sh --build           # 强制重新构建镜像
./deploy.sh --clean           # 清理旧数据并重新部署
./deploy.sh --fix-dimension   # 修复向量维度问题
./deploy.sh --help           # 显示帮助信息
```

## 架构说明

### 🐳 混合部署架构

- **独立Qdrant容器**: 单独运行的向量数据库，使用主机网络（localhost:6333）
- **前端容器**: Nginx + React静态文件，负责UI展示和反向代理
- **后端容器**: FastAPI应用，通过host.docker.internal连接Qdrant
- **网络通信**: 前后端通过docker-compose网络，后端通过主机网络访问Qdrant

### 📁 数据持久化

- **媒体文件**: 主机 `/media` 挂载到容器
- **向量数据库**: 主机 `/media/qdrant` 持久化存储
- **配置文件**: 通过环境变量和卷挂载

### 🌐 网络配置

- 前端端口：3000（HTTP）
- 后端端口：5000（内部）
- Qdrant端口：6333（主机网络）
- 反向代理：Nginx处理 `/api/` 路径到后端

## 文件结构

```
iHomeMedia/
├── backend/                 # FastAPI 后端
│   ├── app/                # 应用代码
│   │   ├── routers/        # API路由
│   │   ├── services/       # 业务逻辑服务
│   │   ├── database/       # 数据库管理
│   │   └── utils/          # 工具函数
│   ├── Dockerfile          # 后端Docker配置
│   ├── requirements.txt    # Python依赖
│   └── start-backend.sh    # 后端启动脚本
├── frontend/               # React + TypeScript 前端
│   ├── src/               # 前端源代码
│   ├── dist/              # 构建输出
│   ├── nginx.docker.conf  # Nginx配置
│   ├── package.json       # Node.js依赖
│   ├── server.py          # 前端代理服务器
│   └── start-frontend.sh  # 前端启动脚本
├── docker-compose.yml     # 前后端服务编排
├── deploy.sh             # 完整部署脚本（推荐）
├── start-app.sh          # 前后端分离启动脚本
├── stop-app.sh           # 应用停止脚本
├── .local.env            # 环境变量配置
└── env.template          # 环境变量模板
```

### 数据目录结构

```
/media/                    # 主机媒体存储目录
├── photos/               # 照片存储
├── videos/               # 视频存储
├── thumbnails/           # 缩略图
└── qdrant/               # 向量数据库数据
```

## 开发模式

### 推荐开发流程

1. **启动数据库**（仅需一次）
   ```bash
   docker run -d --name qdrant-standalone \
     -p 6333:6333 \
     -v /media/qdrant:/qdrant/storage \
     qdrant/qdrant:latest
   ```

2. **使用前后端分离模式开发**
   ```bash
   # 启动应用（推荐选择"同时启动前端和后端"）
   ./start-app.sh
   
   # 开发完成后停止
   ./stop-app.sh
   ```

3. **单独服务调试**
   ```bash
   # 仅启动后端服务 (http://localhost:5000)
   cd backend && ./start-backend.sh
   
   # 仅启动前端服务 (http://localhost:3000)
   cd frontend && ./start-frontend.sh
   ```

### 原生开发环境

如需不使用容器进行开发：

```bash
# 1. 确保Qdrant运行（必需）
docker run -d -p 6333:6333 -v /media/qdrant:/qdrant/storage qdrant/qdrant:latest

# 2. 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 3. 前端开发（新终端）
cd frontend
npm install
npm run dev
```

## 用户凭据

默认登录信息：
- **用户名**: `family`
- **密码**: `123456`

可通过环境变量 `USERNAME` 和 `PASSWORD` 修改

## 技术栈

### 后端
- **FastAPI**: 高性能异步Web框架
- **Qdrant**: 向量数据库，用于AI搜索
- **SQLite**: 关系数据库，存储元数据
- **阿里云DashScope**: 多模态AI服务
- **Uvicorn**: ASGI服务器
- **Docker**: 容器化部署

### 前端
- **React 18**: 用户界面框架
- **TypeScript**: 类型安全的JavaScript
- **Vite**: 快速构建工具
- **Tailwind CSS**: 原子化CSS框架
- **Nginx**: 静态文件服务和反向代理

### 基础设施
- **Docker Compose**: 多容器编排
- **Nginx**: Web服务器和反向代理
- **Linux**: 宿主操作系统

## 浏览器兼容性

- ✅ iPhone Safari（主要支持）
- ✅ Android Chrome
- ✅ 桌面浏览器（Chrome、Firefox、Safari、Edge）
- ✅ iPad Safari

## 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看前后端日志
   docker-compose logs -f
   
   # 查看Qdrant日志
   docker logs -f qdrant-standalone
   
   # 检查端口占用
   netstat -tlnp | grep -E "3000|5000|6333"
   ```

2. **Qdrant连接问题**
   ```bash
   # 检查Qdrant服务状态
   curl http://localhost:6333/
   
   # 重启Qdrant服务
   docker restart qdrant-standalone
   
   # 如果向量维度错误，清理后重建
   ./deploy.sh --fix-dimension
   ```

3. **AI功能不可用**
   - 检查DASHSCOPE_API_KEY是否正确配置
   - 确认网络可以访问阿里云服务
   - 检查后端日志中的AI服务连接错误
   
4. **媒体文件无法访问**
   - 检查 `/media` 目录权限：`ls -la /media`
   - 修复权限：`sudo chown -R $USER:$USER /media && sudo chmod -R 755 /media`
   - 确认目录挂载是否成功

5. **前后端分离模式问题**
   ```bash
   # 检查进程状态
   ./stop-app.sh  # 选择查看当前状态
   
   # 清理僵尸进程
   ./stop-app.sh  # 选择"清理占用端口的所有进程"
   ```

### 重置部署

#### 完整Docker部署重置
```bash
# 停止并清理所有资源
docker-compose down -v
docker stop qdrant-standalone
docker rm qdrant-standalone

# 清理Docker系统
docker system prune -f

# 重新部署
./deploy.sh --clean
```

#### 前后端分离模式重置
```bash
# 停止所有服务
./stop-app.sh

# 重启Qdrant（如果需要）
docker restart qdrant-standalone

# 重新启动应用
./start-app.sh
```

### 数据清理与恢复

```bash
# 仅清理向量数据库（保留媒体文件）
sudo rm -rf /media/qdrant/*
docker restart qdrant-standalone

# 清理缩略图缓存
sudo rm -rf /media/thumbnails/*

# 完全清理重置（谨慎使用）
sudo rm -rf /media/photos/* /media/videos/* /media/thumbnails/* /media/qdrant/*
```

## 注意事项

- 首次启动需要配置阿里云DashScope API密钥
- AI功能需要网络连接到阿里云服务
- 建议在SSD硬盘上运行以获得更好性能
- 媒体文件按日期自动归档存储
- 定期备份 `/media` 目录中的重要数据
- **部署模式选择**：
  - 生产环境推荐使用 `./deploy.sh` 完整Docker部署
  - 开发调试推荐使用 `./start-app.sh` 前后端分离模式
  - Qdrant数据库始终独立运行，确保数据稳定性
- **向量维度问题**：如遇到"expected dim: 1536, got 1024"错误，使用 `./deploy.sh --fix-dimension` 修复

## 安全说明

该应用设计为在家庭局域网内运行，不建议直接暴露到公网。如需外部访问，建议使用：
- VPN服务
- 内网穿透工具（ZeroTier、Tailscale等）
- 反向代理（Nginx + SSL）

## 许可

MIT
