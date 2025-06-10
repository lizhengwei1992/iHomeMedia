# 家庭照片视频管理服务

基于 FastAPI 和 React 构建的家庭照片视频管理系统，支持在本地 Linux 主机上搭建一套可以通过手机浏览器访问的照片和视频管理服务。

## 功能特点

- 手机端（Safari 浏览器）上传照片/视频
- 浏览已上传的照片/视频库
- 文件存储于 Linux 主机本地磁盘
- 所有上传的照片/视频保留原始质量
- 提供基础身份认证（单一账户密码登录）
- 支持 Apple 格式文件（HEIC、MOV 等）

## 系统要求

- 服务端操作系统：Linux（Ubuntu 20.04+）
- Python 3.8+
- Node.js 14+（前端构建需要）
- 局域网环境

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/family_media_app.git
cd family_media_app
```

### 2. 设置环境

使用提供的设置脚本：

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. 启动服务

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

服务将在 `http://your-server-ip:5000` 上运行

## 部署方式

### 方式1: 一体化部署

使用 Docker Compose 进行一体化部署：

```bash
cd docker
docker-compose up -d
```

### 方式2: 前后端分离部署

#### 后端部署

```bash
cd backend
# 安装依赖
pip install -r requirements.txt
# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

#### 前端部署

前端可以独立部署，使用前端目录中提供的部署脚本：

```bash
cd frontend
# 使用部署脚本（Nginx方式）
./deploy.sh
# 或使用Docker方式
./deploy.sh --docker
```

更多前端部署选项，请参考 `frontend/README.md`。

## 文件结构

```
family_media_app/
├── backend/         # FastAPI 后端
├── frontend/        # React + TypeScript 前端
├── media/           # 媒体文件存储
│   ├── photos/      # 照片存储
│   └── videos/      # 视频存储
├── docker/          # Docker 配置
├── nginx/           # Nginx 配置
└── scripts/         # 部署脚本
```

## 用户凭据

默认用户名：`family`
默认密码：`123456`

可在 `backend/app/core/config.py` 中修改

## 浏览器兼容性

- iPhone Safari
- Android Chrome
- 桌面浏览器（Chrome、Firefox、Safari）

## 安全说明

该应用设计为在家庭局域网内运行，不建议暴露到公网。如需外部访问，建议使用 VPN 或内网穿透工具如 ZeroTier、Tailscale 等。

## 许可

MIT
