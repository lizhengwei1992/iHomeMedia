# 配置说明文档

## 🔐 环境变量配置

### 快速开始

1. **复制环境变量模板**
   ```bash
   cp .env.example .local.env
   ```

2. **编辑配置文件**
   ```bash
   # 使用您喜欢的编辑器编辑 .local.env
   nano .local.env
   # 或
   vim .local.env
   ```

3. **填入真实配置值**
   - 必须配置：`DASHSCOPE_API_KEY`
   - 建议配置：`SECRET_KEY`

### 📋 必需配置

#### DASHSCOPE_API_KEY (必需)

阿里云DashScope API密钥，用于多模态embedding服务。

**获取步骤**:
1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 登录您的阿里云账号
3. 进入 **API-KEY管理**
4. 点击 **创建新的API-KEY**
5. 复制生成的API Key

**配置示例**:
```bash
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**注意事项**:
- API Key格式通常以 `sk-` 开头
- 请妥善保管，不要泄露给他人
- 确保账户有足够的调用额度

### 🔒 安全配置

#### SECRET_KEY (强烈建议)

JWT token签名密钥，用于用户认证。

**生成方法**:
```bash
# 方法1: 使用openssl
openssl rand -hex 32

# 方法2: 使用python
python -c "import secrets; print(secrets.token_hex(32))"

# 方法3: 在线生成
# 访问 https://randomkeygen.com/ 生成256位密钥
```

**配置示例**:
```bash
SECRET_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### 🗂️ 可选配置

#### 媒体存储配置

```bash
# 媒体文件存储目录 (默认: /media)
MEDIA_DIR=/media

# 或者使用项目内的目录
# MEDIA_DIR=./media
```

#### 用户认证配置

```bash
# 默认用户名和密码 (默认: family/123456)
DEFAULT_USER=your_username
DEFAULT_PASSWORD=your_secure_password
```

#### 服务器配置

```bash
# 后端服务端口 (默认: 5000)
PORT=5000

# 服务监听地址 (默认: 0.0.0.0)
HOST=0.0.0.0

# 前端CORS允许的域名 (生产环境应限制)
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

#### Qdrant数据库配置

```bash
# 如果使用远程Qdrant服务
QDRANT_URL=http://your-qdrant-server:6333
QDRANT_API_KEY=your_qdrant_api_key_here
```

#### 开发配置

```bash
# 调试模式 (开发环境可启用)
DEBUG=true

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=DEBUG
```

## 📁 配置文件说明

### 文件优先级

1. **`.local.env`** - 本地敏感配置 (优先级最高)
2. **`.env`** - 通用配置
3. **系统环境变量** - 系统级配置
4. **默认值** - 代码中的默认配置

### 配置文件用途

| 文件 | 用途 | 是否提交Git |
|-----|------|------------|
| `.local.env` | 本地敏感配置 | ❌ 不提交 |
| `.env` | 通用配置 | ❌ 不提交 |
| `.env.example` | 配置模板 | ✅ 提交 |

## 🚀 部署配置

### 开发环境

```bash
# .local.env
DASHSCOPE_API_KEY=sk-your-dev-key
SECRET_KEY=your-dev-secret-key
DEBUG=true
LOG_LEVEL=DEBUG
MEDIA_DIR=/media
```

### 测试环境

```bash
# .local.env
DASHSCOPE_API_KEY=sk-your-test-key
SECRET_KEY=your-test-secret-key
DEBUG=false
LOG_LEVEL=INFO
MEDIA_DIR=/media/test
DEFAULT_USER=test_user
DEFAULT_PASSWORD=test_password_123
```

### 生产环境

```bash
# .local.env
DASHSCOPE_API_KEY=sk-your-prod-key
SECRET_KEY=your-super-secure-production-key-256-bits-long
DEBUG=false
LOG_LEVEL=WARNING
MEDIA_DIR=/media/production
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
DEFAULT_USER=admin
DEFAULT_PASSWORD=super_secure_password_123!@#
```

## 🔧 故障排除

### 常见问题

#### 1. API Key错误

**症状**: 启动时提示 "请提供阿里云 API Key"

**解决**:
```bash
# 检查配置文件是否存在
ls -la .local.env

# 检查API Key是否配置
grep DASHSCOPE_API_KEY .local.env

# 确保没有多余的空格或引号
```

#### 2. 配置文件不生效

**症状**: 修改配置后没有变化

**解决**:
```bash
# 检查文件格式 (确保没有BOM头)
file .local.env

# 重启服务
./stop-app.sh && ./start-app.sh

# 检查环境变量是否加载
# 在应用启动日志中查看 "加载本地环境变量" 信息
```

#### 3. 权限问题

**症状**: 无法读取配置文件

**解决**:
```bash
# 检查文件权限
ls -la .local.env

# 修正权限
chmod 600 .local.env
```

## 🛡️ 安全最佳实践

### 1. 配置文件安全

- ✅ 确保 `.local.env` 在 `.gitignore` 中
- ✅ 设置适当的文件权限 (`chmod 600`)
- ✅ 定期轮换API密钥和SECRET_KEY
- ❌ 不要在代码或日志中硬编码敏感信息

### 2. API Key管理

- ✅ 使用独立的API Key用于不同环境
- ✅ 监控API调用量，设置预警
- ✅ 定期检查API Key的权限范围
- ❌ 不要在前端代码中暴露API Key

### 3. 密码安全

- ✅ 生产环境使用强密码
- ✅ 定期更换默认密码
- ✅ 考虑使用外部认证系统
- ❌ 不要使用默认密码 `123456`

## 📞 获取帮助

如果在配置过程中遇到问题：

1. **检查日志**: 启动应用时查看控制台输出
2. **验证配置**: 使用 `./start-app.sh` 选项1测试后端API
3. **查看文档**: 阅读 [开发指南](DEVELOPMENT.md)
4. **阿里云支持**: 访问 [DashScope文档](https://help.aliyun.com/zh/dashscope/)

### 配置验证脚本

```bash
# 检查配置是否正确
python -c "
from backend.app.core.config import settings
print('DashScope API Key:', 'OK' if settings.DASHSCOPE_API_KEY else 'MISSING')
print('Secret Key:', 'OK' if settings.SECRET_KEY != 'your-secret-key-for-jwt-token' else 'DEFAULT')
print('Media Dir:', settings.MEDIA_DIR if hasattr(settings, 'MEDIA_DIR') else 'DEFAULT')
"
``` 