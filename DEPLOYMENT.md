# iHomeMedia 部署文档

## 架构概述

本项目采用"前后端分离 + Nginx 反向代理"的Docker容器化部署架构：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端容器       │    │   后端容器       │    │  Qdrant容器     │
│  (React+Nginx)  │    │   (FastAPI)     │    │  (向量数据库)    │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │   Nginx   │──┼────┼──│  FastAPI  │──┼────┼──│  Qdrant   │  │
│  │           │  │    │  │           │  │    │  │           │  │
│  │ 静态文件   │  │    │  │    API     │  │    │  │  向量搜索  │  │
│  │ 反向代理   │  │    │  │   服务     │  │    │  │           │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                │
                     ┌─────────────────┐
                     │   主机文件系统   │
                     │                 │
                     │  /media/        │
                     │  ├── photos/    │
                     │  ├── videos/    │
                     │  ├── thumbnails/│
                     │  └── qdrant/    │
                     └─────────────────┘
```

## 环境要求

### 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **内存**: 最少 4GB (推荐 8GB+)
- **存储**: 最少 20GB 可用空间
- **网络**: 能够访问外网 (用于下载Docker镜像)

### 软件依赖
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **curl**: 用于健康检查

### 存储要求
- **媒体存储**: `/media` 目录 (可以是挂载的外部存储)
- **向量数据库**: `/media/qdrant` 子目录

## 部署前准备

### 1. 安装Docker和Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 准备媒体存储目录

```bash
# 创建媒体存储目录
sudo mkdir -p /media
sudo mkdir -p /media/photos
sudo mkdir -p /media/videos
sudo mkdir -p /media/thumbnails
sudo mkdir -p /media/qdrant

# 设置权限
sudo chmod -R 755 /media
```

### 3. 配置环境变量

复制并编辑环境变量文件：

```bash
# 如果没有 .local.env 文件，请创建它
cp .local.env.example .local.env  # 如果有示例文件
# 或者直接创建
nano .local.env
```

`.local.env` 文件内容示例：
```bash
# 阿里云DashScope API Key (必需)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# JWT签名密钥 (生产环境必须修改)
SECRET_KEY=your_super_secret_key_here

# 媒体文件存储目录
MEDIA_DIR=/media

# 搜索配置
TEXT_TO_TEXT_THRESHOLD=0.8   
TEXT_TO_IMAGE_THRESHOLD=0.2
IMAGE_SEARCH_THRESHOLD=0.5
```

## 部署步骤

### 方法一：使用部署脚本 (推荐)

1. **赋予脚本执行权限**
```bash
chmod +x deploy.sh stop.sh manage.sh
```

2. **运行部署脚本**
```bash
./deploy.sh
```

3. **等待部署完成**
脚本会自动完成以下步骤：
- 检查系统要求
- 准备媒体目录
- 构建Docker镜像
- 启动所有服务
- 等待服务健康检查
- 显示部署结果

### 方法二：手动部署

1. **构建和启动服务**
```bash
docker-compose up --build -d
```

2. **检查服务状态**
```bash
docker-compose ps
```

3. **查看日志**
```bash
docker-compose logs -f
```

## 服务访问

部署成功后，可以通过以下地址访问服务：

- **前端应用**: http://localhost:3000
- **API文档**: http://localhost:3000/api/v1/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 服务管理

### 查看服务状态
```bash
./manage.sh status
```

### 查看日志
```bash
./manage.sh logs          # 所有服务日志
./manage.sh logs backend  # 后端日志
./manage.sh logs frontend # 前端日志
./manage.sh logs qdrant   # Qdrant日志
```

### 重启服务
```bash
./manage.sh restart           # 重启所有服务
./manage.sh restart backend   # 重启后端服务
```

### 停止服务
```bash
./stop.sh              # 停止服务
./stop.sh --remove     # 停止并移除容器
```

### 进入容器
```bash
./manage.sh exec backend bash    # 进入后端容器
./manage.sh exec frontend sh     # 进入前端容器
```

## 数据管理

### 备份数据
```bash
./manage.sh backup
```

### 数据存储位置
- **媒体文件**: `/media/photos`, `/media/videos`
- **缩略图**: `/media/thumbnails`
- **向量数据库**: `/media/qdrant`

## 故障排除

### 常见问题

1. **端口占用**
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :6333

# 停止占用端口的服务
sudo systemctl stop nginx  # 如果系统安装了nginx
```

2. **权限问题**
```bash
# 修复媒体目录权限
sudo chown -R $USER:$USER /media
sudo chmod -R 755 /media
```

3. **磁盘空间不足**
```bash
# 清理Docker资源
./manage.sh cleanup

# 查看磁盘使用情况
df -h
du -sh /media/*
```

4. **服务启动失败**
```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs qdrant

# 检查容器状态
docker-compose ps
```

### 健康检查命令

```bash
# 检查Qdrant
curl http://localhost:6333/health

# 检查后端API
curl http://localhost:3000/api/v1/ping

# 检查前端
curl http://localhost:3000/health
```

## 性能优化

### 生产环境建议

1. **资源限制**
在 `docker-compose.yml` 中添加资源限制：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
```

2. **日志轮转**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

3. **缓存策略**
- 前端静态文件已配置缓存策略
- 媒体文件设置7天缓存
- API请求不缓存

## 安全注意事项

1. **更改默认密钥**
- 修改 `.local.env` 中的 `SECRET_KEY`
- 使用强密码保护管理账户

2. **防火墙配置**
```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 6333/tcp  # 仅在需要外部访问Qdrant时
```

3. **HTTPS配置**
生产环境建议配置HTTPS，可以在nginx前端添加SSL证书。

## 更新与维护

### 更新应用
```bash
./manage.sh update
```

### 定期维护
```bash
# 清理未使用的资源
./manage.sh cleanup

# 备份数据
./manage.sh backup

# 检查日志大小
du -sh /var/lib/docker/containers/*/
```

## 技术支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查应用日志：`./manage.sh logs`
3. 查看系统资源使用情况：`htop`, `df -h`
4. 提供详细的错误信息和环境描述 