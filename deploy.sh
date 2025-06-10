#!/bin/bash

# iHomeMedia 部署脚本
# 使用前后端分离架构 + Nginx反向代理部署

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

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose 未安装，请先安装docker-compose"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f ".local.env" ]; then
        log_error ".local.env 文件不存在，请先创建并配置环境变量"
        log_info "可以复制 .local.env 模板并修改相应配置"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 准备媒体目录
prepare_media_dirs() {
    log_info "准备媒体目录..."
    
    # 检查/media目录是否存在
    if [ ! -d "/media" ]; then
        log_error "/media 目录不存在，请确保媒体存储目录已正确挂载"
        exit 1
    fi
    
    # 创建必要的子目录
    sudo mkdir -p /media/photos
    sudo mkdir -p /media/videos
    sudo mkdir -p /media/thumbnails
    sudo mkdir -p /media/qdrant
    
    # 设置权限（如果需要）
    sudo chmod -R 755 /media
    
    log_success "媒体目录准备完成"
}

# 构建和启动服务
deploy_services() {
    log_info "开始构建和部署服务..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down --remove-orphans
    
    # 清理旧的镜像（可选）
    if [ "$1" == "--clean" ]; then
        log_info "清理旧的Docker镜像..."
        docker system prune -f
    fi
    
    # 构建和启动服务
    log_info "构建并启动服务..."
    docker-compose up --build -d
    
    log_success "服务部署完成"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    # 等待Qdrant启动
    log_info "等待Qdrant数据库启动..."
    timeout=180
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:6333/ | grep -q "qdrant" &> /dev/null; then
            log_success "Qdrant数据库启动成功"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Qdrant数据库启动超时"
        exit 1
    fi
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    timeout=180
    while [ $timeout -gt 0 ]; do
        backend_status=$(docker-compose ps backend --format "table {{.Status}}" | tail -n 1)
        if [[ "$backend_status" == *"healthy"* ]]; then
            log_success "后端服务启动成功"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "后端服务启动超时"
        exit 1
    fi
    
    # 等待前端启动
    log_info "等待前端服务启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:3000/health &> /dev/null; then
            log_success "前端服务启动成功"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "前端服务启动超时"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 iHomeMedia 部署成功！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📱 应用访问信息："
    echo "   前端应用: http://localhost:3000"
    echo "   API文档:  http://localhost:3000/api/v1/docs"
    echo ""
    echo "🗄️ 数据库访问信息："
    echo "   Qdrant Dashboard: http://localhost:6333/dashboard"
    echo ""
    echo "📁 数据存储路径："
    echo "   媒体文件: /media/"
    echo "   向量数据库: /media/qdrant/"
    echo ""
    echo "🐳 Docker 服务状态："
    docker-compose ps
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 管理命令："
    echo "   查看日志: docker-compose logs -f"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
    echo "   查看状态: docker-compose ps"
}

# 主函数
main() {
    echo "🚀 开始部署 iHomeMedia..."
    echo ""
    
    check_requirements
    prepare_media_dirs
    deploy_services $1
    wait_for_services
    show_deployment_info
    
    log_success "部署完成！请使用 http://localhost:3000 访问应用"
}

# 显示帮助信息
show_help() {
    echo "iHomeMedia 部署脚本"
    echo ""
    echo "用法:"
    echo "  $0                 # 正常部署"
    echo "  $0 --clean        # 清理旧镜像后部署"
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
        main $1
        ;;
esac 