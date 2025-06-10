# 🚀 快速配置指南

## 1分钟配置阿里云API Key

### 🎯 一键配置 (推荐)

```bash
# 运行配置向导
./setup-config.sh
```

配置向导会自动：
- 创建 `.local.env` 配置文件
- 引导您输入阿里云DashScope API Key
- 自动生成安全的JWT密钥
- 设置正确的文件权限

### 📝 手动配置

如果您prefer手动配置：

1. **复制配置模板**
   ```bash
   cp .env.example .local.env
   ```

2. **编辑配置文件**
   ```bash
   nano .local.env
   ```

3. **填入您的API Key**
   ```bash
   # 将 your_dashscope_api_key_here 替换为您的真实API Key
   DASHSCOPE_API_KEY=sk-your-real-api-key-here
   ```

4. **设置文件权限**
   ```bash
   chmod 600 .local.env
   ```

### 🔑 获取阿里云API Key

1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 登录您的阿里云账号
3. 进入 **API-KEY管理**
4. 点击 **创建新的API-KEY**
5. 复制生成的API Key (格式: `sk-xxxxxx`)

### ✅ 验证配置

```bash
# 测试配置是否正确
cd backend
python3 -c "from app.core.config import settings; print('✅ API Key配置成功' if settings.DASHSCOPE_API_KEY else '❌ API Key未配置')"
cd ..
```

应该看到：
```
加载本地环境变量: /path/to/.local.env
✅ API Key配置成功
```

### 🎉 启动应用

```bash
# 启动应用
./start-app.sh
```

选择选项3或4 (支持媒体文件代理的模式)

---

## 🛡️ 安全提醒

- ✅ `.local.env` 已添加到 `.gitignore`，不会被提交到Git
- ✅ 配置文件权限已设置为 `600` (仅所有者可读写)
- ❌ 请勿在代码或日志中暴露API Key
- 🔄 建议定期更换API Key

## 📚 更多信息

- 完整配置文档: [CONFIGURATION.md](CONFIGURATION.md)
- 开发指南: [DEVELOPMENT.md](DEVELOPMENT.md)
- 故障排除: [CONFIGURATION.md#故障排除](CONFIGURATION.md#故障排除) 