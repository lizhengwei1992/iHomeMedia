#!/bin/bash

# 配置设置脚本
# 帮助用户快速配置阿里云DashScope API Key和其他环境变量

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查文件是否存在
check_file_exists() {
    if [ -f "$1" ]; then
        return 0
    else
        return 1
    fi
}

echo "🔧 家庭媒体应用 - 环境变量配置向导"
echo "=================================="
echo

# 检查.local.env是否已存在
if check_file_exists ".local.env"; then
    print_warning ".local.env 文件已存在"
    echo
    read -p "是否要重新配置？[y/N]: " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "配置取消，退出脚本"
        exit 0
    fi
    echo
fi

# 复制模板文件
if check_file_exists ".env.example"; then
    print_info "复制 .env.example 到 .local.env ..."
    cp .env.example .local.env
    print_success "模板文件复制完成"
else
    print_error ".env.example 文件不存在，请先创建模板文件"
    exit 1
fi

echo

# 配置DashScope API Key
print_info "配置阿里云DashScope API Key"
echo "获取地址: https://dashscope.console.aliyun.com/"
echo "登录阿里云控制台 -> DashScope -> API-KEY管理 -> 创建新的API-KEY"
echo

while true; do
    read -p "请输入您的DashScope API Key: " api_key
    
    if [ -z "$api_key" ]; then
        print_error "API Key不能为空，请重新输入"
        continue
    fi
    
    if [[ ! $api_key =~ ^sk- ]]; then
        print_warning "API Key格式通常以 'sk-' 开头，您输入的格式可能不正确"
        read -p "是否继续使用此API Key？[y/N]: " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            continue
        fi
    fi
    
    break
done

# 更新API Key
if command -v sed > /dev/null; then
    sed -i "s/your_dashscope_api_key_here/$api_key/g" .local.env
    print_success "DashScope API Key 配置完成"
else
    print_error "sed 命令不可用，请手动编辑 .local.env 文件"
fi

echo

# 配置Secret Key
print_info "生成JWT签名密钥"
if command -v openssl > /dev/null; then
    secret_key=$(openssl rand -hex 32)
    sed -i "s/your-super-secret-jwt-key/$secret_key/g" .local.env
    print_success "JWT Secret Key 自动生成并配置完成"
elif command -v python3 > /dev/null; then
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-super-secret-jwt-key/$secret_key/g" .local.env
    print_success "JWT Secret Key 自动生成并配置完成"
else
    print_warning "无法自动生成Secret Key，请手动设置"
    echo "您可以访问 https://randomkeygen.com/ 生成一个256位密钥"
fi

echo

# 设置文件权限
print_info "设置文件权限为只读（600）..."
chmod 600 .local.env
print_success "文件权限设置完成"

echo

# 验证配置
print_info "验证配置..."
if grep -q "your_dashscope_api_key_here" .local.env; then
    print_error "DashScope API Key 尚未配置"
else
    print_success "DashScope API Key 配置正确"
fi

if grep -q "your-super-secret-jwt-key" .local.env; then
    print_warning "JWT Secret Key 使用默认值，建议修改"
else
    print_success "JWT Secret Key 配置正确"
fi

echo

# 显示配置文件位置
print_success "配置完成！"
echo
print_info "配置文件位置: $(pwd)/.local.env"
print_info "您可以使用以下命令编辑配置："
echo "  nano .local.env"
echo "  vim .local.env"
echo

# 显示下一步操作
print_info "下一步操作："
echo "1. 启动应用: ./start-app.sh"
echo "2. 查看配置文档: cat CONFIGURATION.md"
echo "3. 检查配置是否生效，在应用启动时查看日志"

echo

# 安全提醒
print_warning "安全提醒："
echo "- .local.env 文件包含敏感信息，已添加到 .gitignore"
echo "- 请勿将此文件提交到Git仓库"
echo "- 定期更换API Key和Secret Key"

echo
print_success "配置向导完成！" 