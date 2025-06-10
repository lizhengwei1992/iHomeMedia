#!/bin/bash

# iHomeMedia 管理脚本

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

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    echo ""
    
    log_info "服务健康状态:"
    echo "Qdrant: $(curl -s http://localhost:6333/health 2>/dev/null && echo "✅ 正常" || echo "❌ 异常")"
    echo "后端:   $(curl -s http://localhost:5000/ping 2>/dev/null | grep -q "ok" && echo "✅ 正常" || echo "❌ 异常")"
    echo "前端:   $(curl -s http://localhost:3000/health 2>/dev/null && echo "✅ 正常" || echo "❌ 异常")"
}

# 查看日志
show_logs() {
    if [ -z "$1" ]; then
        log_info "显示所有服务日志..."
        docker-compose logs -f
    else
        log_info "显示 $1 服务日志..."
        docker-compose logs -f "$1"
    fi
}

# 重启服务
restart_service() {
    if [ -z "$1" ]; then
        log_info "重启所有服务..."
        docker-compose restart
    else
        log_info "重启 $1 服务..."
        docker-compose restart "$1"
    fi
    log_success "重启完成"
}

# 执行容器内命令
exec_command() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        log_error "用法: manage.sh exec <service> <command>"
        exit 1
    fi
    
    log_info "在 $1 容器中执行: $2"
    docker-compose exec "$1" $2
}

# 备份数据
backup_data() {
    backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    log_info "创建备份目录: $backup_dir"
    mkdir -p "$backup_dir"
    
    # 备份Qdrant数据
    if [ -d "/media/qdrant" ]; then
        log_info "备份Qdrant数据..."
        cp -r /media/qdrant "$backup_dir/"
    fi
    
    # 备份媒体文件（可选）
    read -p "是否备份媒体文件？(y/N): " backup_media
    if [[ $backup_media =~ ^[Yy]$ ]]; then
        log_info "备份媒体文件..."
        cp -r /media/photos "$backup_dir/" 2>/dev/null || true
        cp -r /media/videos "$backup_dir/" 2>/dev/null || true
        cp -r /media/thumbnails "$backup_dir/" 2>/dev/null || true
    fi
    
    log_success "备份完成: $backup_dir"
}

# 清理资源
cleanup() {
    log_warning "这将清理未使用的Docker资源..."
    read -p "确认继续？(y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        docker system prune -f
        docker volume prune -f
        log_success "清理完成"
    else
        log_info "取消清理"
    fi
}

# 更新服务
update_services() {
    log_info "更新服务..."
    
    # 拉取最新代码（如果是Git仓库）
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull
    fi
    
    # 重新构建和部署
    log_info "重新构建服务..."
    docker-compose down
    docker-compose up --build -d
    
    log_success "更新完成"
}

# 显示帮助信息
show_help() {
    echo "iHomeMedia 管理脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  status              # 显示服务状态"
    echo "  logs [service]      # 查看日志（可指定服务名）"
    echo "  restart [service]   # 重启服务（可指定服务名）"
    echo "  exec <service> <cmd># 在容器中执行命令"
    echo "  backup              # 备份数据"
    echo "  cleanup             # 清理Docker资源"
    echo "  update              # 更新服务"
    echo "  help                # 显示帮助信息"
    echo ""
    echo "服务名称:"
    echo "  qdrant              # Qdrant向量数据库"
    echo "  backend             # 后端API服务"
    echo "  frontend            # 前端Nginx服务"
    echo ""
    echo "示例:"
    echo "  $0 status           # 查看所有服务状态"
    echo "  $0 logs backend     # 查看后端日志"
    echo "  $0 restart frontend # 重启前端服务"
    echo "  $0 exec backend bash# 进入后端容器"
}

# 处理命令行参数
case "$1" in
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    restart)
        restart_service "$2"
        ;;
    exec)
        exec_command "$2" "${@:3}"
        ;;
    backup)
        backup_data
        ;;
    cleanup)
        cleanup
        ;;
    update)
        update_services
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac 