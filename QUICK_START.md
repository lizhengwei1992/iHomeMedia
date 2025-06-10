# iHomeMedia 快速启动指南

## 🚀 一键部署

### 前置要求
- 已安装 Docker 和 Docker Compose
- 系统有 `/media` 目录用于存储媒体文件
- 已配置 `.local.env` 环境变量文件

### 一键部署命令

```bash
# 1. 克隆项目（如果还没有）
git clone <repository-url>
cd iHomeMedia

# 2. 配置环境变量
nano .local.env

# 3. 一键部署
./deploy.sh
```

### 环境变量配置 (.local.env)

```bash
# 阿里云DashScope API Key (必需 - 用于AI搜索功能)
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here

# JWT签名密钥 (建议修改)
SECRET_KEY=your-super-secret-key-change-in-production

# 媒体文件存储目录
MEDIA_DIR=/media

# 搜索阈值配置（可选）
TEXT_TO_TEXT_THRESHOLD=0.8   
TEXT_TO_IMAGE_THRESHOLD=0.2
IMAGE_SEARCH_THRESHOLD=0.5
```

## 📦 项目架构

```
iHomeMedia/
├── backend/               # FastAPI 后端
│   ├── app/              # 应用代码
│   ├── requirements.txt  # Python依赖
│   └── Dockerfile        # 后端镜像
├── frontend/             # React 前端
│   ├── src/              # React源代码
│   ├── Dockerfile        # 前端镜像（含Nginx）
│   └── nginx.docker.conf # Nginx配置
├── docker-compose.yml    # 容器编排文件
├── deploy.sh            # 部署脚本
├── stop.sh              # 停止脚本
├── manage.sh            # 管理脚本
└── DEPLOYMENT.md        # 详细部署文档
```

## 🌟 部署后验证

### 1. 检查服务状态
```bash
./manage.sh status
```

### 2. 访问应用
- **前端应用**: http://localhost:3000
- **API文档**: http://localhost:3000/api/v1/docs
- **向量数据库**: http://localhost:6333/dashboard

### 3. 测试功能
1. 打开前端应用
2. 登录（用户名: family, 密码: 123456）
3. 上传测试照片
4. 尝试搜索功能

## 🔧 常用管理命令

```bash
# 查看所有服务状态
./manage.sh status

# 查看服务日志
./manage.sh logs
./manage.sh logs backend   # 仅后端日志

# 重启服务
./manage.sh restart
./manage.sh restart backend  # 仅重启后端

# 停止服务
./stop.sh

# 备份数据
./manage.sh backup

# 进入容器调试
./manage.sh exec backend bash
```

## 📁 数据存储位置

```
/media/
├── photos/      # 原始照片文件
├── videos/      # 原始视频文件
├── thumbnails/  # 缩略图文件
└── qdrant/      # 向量数据库存储
```

## ⚠️ 常见问题

### 1. 端口被占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :6333

# 停止冲突服务
sudo systemctl stop nginx
```

### 2. 权限问题
```bash
sudo chmod -R 755 /media
```

### 3. 内存不足
```bash
# 检查内存使用
free -h

# 清理Docker资源
./manage.sh cleanup
```

### 4. 服务启动失败
```bash
# 查看详细错误日志
./manage.sh logs backend
./manage.sh logs frontend
```

## 🔄 更新应用

```bash
# 拉取最新代码并重新部署
./manage.sh update
```

## 🛑 完全清理

如果需要完全清理并重新开始：

```bash
# 停止并移除所有容器
./stop.sh --remove

# 清理Docker资源
docker system prune -a -f

# 清理媒体文件（谨慎操作！）
sudo rm -rf /media/qdrant/*
sudo rm -rf /media/thumbnails/*
```

## 📞 技术支持

如果遇到问题：

1. 查看 `DEPLOYMENT.md` 获取详细文档
2. 检查日志：`./manage.sh logs`
3. 验证环境变量配置
4. 确保系统资源充足（内存 > 4GB）

---

**享受使用 iHomeMedia！** 🎉 