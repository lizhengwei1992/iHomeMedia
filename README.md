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

- 服务端操作系统：Linux（Ubuntu 20.04+）
- Python 3.8+
- Node.js 16+（前端构建需要）
- 局域网环境
- 阿里云DashScope API密钥（用于AI功能）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/family_media_app.git
cd family_media_app
```

### 2. 环境配置

#### 后端环境设置

```bash
cd backend
pip install -r requirements.txt
```

配置环境变量（创建 `.local.env` 文件）：

```bash
# API配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 数据库配置（可选，默认使用SQLite）
DATABASE_URL=sqlite:///./media_app.db

# Qdrant向量数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 其他配置
SECRET_KEY=your-secret-key-here
USERNAME=family
PASSWORD=123456
```

#### 前端环境设置

```bash
cd frontend
npm install
npm run build
```

### 3. 启动服务

使用便捷启动脚本：

```bash
chmod +x start-app.sh
./start-app.sh
```

选择启动模式：
- 选项1: 仅启动后端 (http://localhost:5000)
- 选项2: 仅启动前端 (http://localhost:3000)  
- 选项3: 同时启动前端和后端（推荐）

访问地址：`http://your-server-ip:3000`

## 开发模式

### 后端开发

```bash
cd backend
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### 前端开发

```bash
cd frontend
# 安装依赖
npm install

# 启动开发服务器（热更新）
npm run dev
```

### 联合开发

使用启动脚本同时运行前后端：

```bash
./start-app.sh
# 选择选项3：同时启动前端和后端
```

## 文件结构

```
family_media_app/
├── backend/         # FastAPI 后端
│   ├── app/         # 应用代码
│   │   ├── routers/ # API路由
│   │   ├── services/ # 业务逻辑服务
│   │   ├── database/ # 数据库管理
│   │   └── utils/   # 工具函数
│   └── requirements.txt
├── frontend/        # React + TypeScript 前端
│   ├── src/         # 前端源代码
│   ├── dist/        # 构建输出
│   └── package.json
├── media/           # 媒体文件存储
│   ├── photos/      # 照片存储
│   ├── videos/      # 视频存储
│   ├── thumbnails/  # 缩略图
│   └── descriptions.json # 描述文件
└── start-app.sh     # 便捷启动脚本
```

## 用户凭据

默认用户名：`family`
默认密码：`123456`

可通过环境变量 `USERNAME` 和 `PASSWORD` 修改

## 技术栈

### 后端
- **FastAPI**: 高性能异步Web框架
- **Qdrant**: 向量数据库，用于AI搜索
- **SQLite**: 关系数据库，存储元数据
- **阿里云DashScope**: 多模态AI服务
- **Uvicorn**: ASGI服务器

### 前端
- **React 18**: 用户界面框架
- **TypeScript**: 类型安全的JavaScript
- **Vite**: 快速构建工具
- **Tailwind CSS**: 原子化CSS框架

## 浏览器兼容性

- ✅ iPhone Safari（主要支持）
- ✅ Android Chrome
- ✅ 桌面浏览器（Chrome、Firefox、Safari、Edge）
- ✅ iPad Safari

## 注意事项

- 首次启动需要配置阿里云DashScope API密钥
- AI功能需要网络连接到阿里云服务
- 建议在SSD硬盘上运行以获得更好性能
- 媒体文件按日期自动归档存储

## 安全说明

该应用设计为在家庭局域网内运行，不建议直接暴露到公网。如需外部访问，建议使用：
- VPN服务
- 内网穿透工具（ZeroTier、Tailscale等）
- 反向代理（Nginx + SSL）

## 许可

MIT
