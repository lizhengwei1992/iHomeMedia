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
cp env.template .env
```

编辑 `.env` 文件，配置必要的环境变量：

```bash
# 阿里云DashScope API密钥（必需）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 用户认证信息
USERNAME=family
PASSWORD=123456

# 其他配置项根据需要调整
SECRET_KEY=your-secret-key-here
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### 4. 一键部署

使用部署脚本快速启动所有服务：

```bash
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动：
- ✅ 检查系统要求
- ✅ 准备媒体目录
- ✅ 构建Docker镜像
- ✅ 启动所有服务（Qdrant + 后端 + 前端）
- ✅ 等待服务就绪
- ✅ 显示访问信息

### 5. 访问应用

部署成功后，通过以下地址访问：

- **前端应用**: http://localhost:3000
- **API文档**: http://localhost:3000/api/v1/docs
- **Qdrant仪表板**: http://localhost:6333/dashboard

## 服务管理

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
./stop.sh
# 或手动停止
docker-compose down

# 重启服务
docker-compose restart

# 完全重新构建部署
./deploy.sh --clean
```

### 日常管理

使用管理脚本进行日常操作：

```bash
chmod +x manage.sh
./manage.sh
```

管理脚本提供以下功能：
- 查看服务状态
- 查看实时日志
- 重启指定服务
- 数据备份
- 系统清理

## 架构说明

### 🐳 容器化架构

- **前端容器**: Nginx + React静态文件，负责UI展示和反向代理
- **后端容器**: FastAPI应用，提供API服务
- **向量数据库**: Qdrant容器，存储AI向量数据

### 📁 数据持久化

- **媒体文件**: 主机 `/media` 挂载到容器
- **向量数据库**: 主机 `/media/qdrant` 持久化存储
- **配置文件**: 通过环境变量和卷挂载

### 🌐 网络配置

- 前端端口：3000（HTTP）
- Qdrant端口：6333-6334
- 内部网络：ihomemedia-network
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
│   └── requirements.txt    # Python依赖
├── frontend/               # React + TypeScript 前端
│   ├── src/               # 前端源代码
│   ├── dist/              # 构建输出
│   ├── nginx.docker.conf  # Nginx配置
│   └── package.json       # Node.js依赖
├── docker-compose.yml     # Docker服务编排
├── deploy.sh             # 一键部署脚本
├── stop.sh               # 停止服务脚本
├── manage.sh             # 日常管理脚本
├── .env                  # 环境变量配置
├── env.template          # 环境变量模板
├── DEPLOYMENT.md         # 详细部署文档
└── QUICK_START.md        # 快速启动指南
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

### 本地开发环境

如需进行开发，可以单独启动服务：

```bash
# 启动Qdrant（开发环境需要）
docker run -p 6333:6333 qdrant/qdrant:v1.7.0

# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 前端开发（新终端）
cd frontend
npm install
npm run dev
```

### 容器化开发

推荐使用容器进行开发，保持环境一致性：

```bash
# 只启动Qdrant和后端，前端使用开发模式
docker-compose up qdrant backend -d

# 前端开发模式
cd frontend && npm run dev
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
   # 查看详细日志
   docker-compose logs -f
   
   # 检查端口占用
   netstat -tlnp | grep 3000
   ```

2. **AI功能不可用**
   - 检查DASHSCOPE_API_KEY是否正确配置
   - 确认网络可以访问阿里云服务
   
3. **媒体文件无法访问**
   - 检查 `/media` 目录权限
   - 确认目录挂载是否成功

### 重置部署

如需完全重置：

```bash
# 停止并清理所有资源
docker-compose down -v
docker system prune -f

# 重新部署
./deploy.sh --clean
```

详细的故障排除指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 注意事项

- 首次启动需要配置阿里云DashScope API密钥
- AI功能需要网络连接到阿里云服务
- 建议在SSD硬盘上运行以获得更好性能
- 媒体文件按日期自动归档存储
- 定期备份 `/media` 目录中的重要数据

## 安全说明

该应用设计为在家庭局域网内运行，不建议直接暴露到公网。如需外部访问，建议使用：
- VPN服务
- 内网穿透工具（ZeroTier、Tailscale等）
- 反向代理（Nginx + SSL）

## 许可

MIT
