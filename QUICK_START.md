# 🚀 快速开始指南

## 一键启动

```bash
# 启动所有服务
./start-app.sh

# 停止所有服务  
./stop-app.sh
```

## ⚡ 开发测试流程

### 🔄 完整重启
```bash
./stop-app.sh && ./start-app.sh
```

### 🛠️ 开发模式
```bash
./start-app.sh
# 选择 4 - 开发模式(支持媒体文件代理)
```

### 🔧 仅重启后端
```bash
./stop-app.sh  # 选择 3 - 仅停止后端
./start-app.sh # 选择 1 - 仅启动后端
```

### 🎨 前端热更新
```bash
./start-app.sh
# 选择 5 - Vite开发模式(热更新，但不支持媒体预览)
```

## 📱 访问地址

- **主应用**: http://localhost:3000
- **API文档**: http://localhost:5000/docs

## 🆘 常见操作

### 端口被占用
```bash
./stop-app.sh
# 选择 5 - 清理端口
```

### 权限问题
```bash
./start-app.sh  
# 选择 6 - 特权模式
```

### 服务卡死
```bash
./stop-app.sh
# 选择 2 - 强制停止
```

更多详细信息请查看 [开发指南](DEVELOPMENT.md) 