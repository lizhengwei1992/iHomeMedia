#!/bin/bash

# iHomeMedia 停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止服务
stop_services() {
    log_info "停止 iHomeMedia 服务..."
    
    if [ "$1" == "--remove" ]; then
        log_info "停止并移除所有容器..."
        docker-compose down --remove-orphans
        log_success "服务已停止并移除"
    else
        log_info "停止容器（保留容器）..."
        docker-compose stop
        log_success "服务已停止"
    fi
}

# 显示帮助信息
show_help() {
    echo "iHomeMedia 停止脚本"
    echo ""
    echo "用法:"
    echo "  $0                 # 停止服务（保留容器）"
    echo "  $0 --remove        # 停止并移除容器"
    echo "  $0 --help         # 显示帮助信息"
    echo ""
}

# 处理命令行参数
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        stop_services $1
        ;;
esac 