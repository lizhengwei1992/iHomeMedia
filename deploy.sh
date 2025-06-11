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
    
    # 设置正确的所有者和权限，确保容器可以写入
    sudo chown -R $USER:$USER /media/photos /media/videos /media/thumbnails
    sudo chmod -R 755 /media/photos /media/videos /media/thumbnails
    sudo chmod -R 755 /media/qdrant
    
    log_success "媒体目录准备完成"
}

# 独立部署Qdrant数据库
deploy_qdrant_standalone() {
    log_info "独立部署Qdrant向量数据库..."
    
    # 停止现有的Qdrant容器
    if docker ps -a | grep -q "qdrant-standalone"; then
        log_info "停止现有的Qdrant容器..."
        docker stop qdrant-standalone >/dev/null 2>&1 || true
        docker rm qdrant-standalone >/dev/null 2>&1 || true
    fi
    
    # 清理旧的向量数据（如果是清理模式或需要修复向量维度）
    if [ "$1" == "--clean" ] || [ "$1" == "--fix-dimension" ]; then
        log_warning "清理旧的Qdrant数据..."
        sudo rm -rf /media/qdrant/* 2>/dev/null || true
        log_info "Qdrant数据已清理，将重新创建集合"
    fi
    
    # 启动新的Qdrant容器（使用主机网络）
    log_info "启动独立的Qdrant容器..."
    
    docker run -d \
        --name qdrant-standalone \
        --restart unless-stopped \
        -p 6333:6333 \
        -v /media/qdrant:/qdrant/storage \
        qdrant/qdrant:latest
    
    # 等待Qdrant启动
    log_info "等待Qdrant数据库启动..."
    timeout=60
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
    
    # 检查集合状态并自动修复向量维度问题
    log_info "检查Qdrant集合状态..."
    sleep 3  # 等待服务完全启动
    
    # 检查是否存在集合且维度正确
    collection_info=$(curl -s http://localhost:6333/collections/media_embeddings 2>/dev/null || echo "")
    if [[ "$collection_info" == *"1536"* ]]; then
        log_warning "检测到旧的1536维向量集合，需要重新创建为1024维集合"
        log_info "删除旧集合..."
        curl -s -X DELETE http://localhost:6333/collections/media_embeddings >/dev/null 2>&1 || true
        log_info "旧集合已删除，后端启动时将自动创建新的1024维集合"
    elif [[ "$collection_info" == *"not found"* ]] || [[ "$collection_info" == "" ]]; then
        log_info "集合不存在，后端启动时将自动创建"
    else
        log_info "集合状态正常"
    fi
    
    log_success "独立Qdrant数据库部署完成"
}

# 构建和启动服务
deploy_services() {
    log_info "开始构建和部署服务..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down --remove-orphans
    
    # 清理旧的镜像（仅在--clean模式下）
    if [ "$1" == "--clean" ]; then
        log_info "清理旧的Docker镜像..."
        docker system prune -f
    fi
    
    # 构建和启动服务
    if [ "$1" == "--build" ] || [ "$1" == "--clean" ]; then
        log_info "强制重新构建并启动服务..."
        docker-compose up --build -d
    else
        log_info "启动服务（仅在必要时重建）..."
        docker-compose up -d
    fi
    
    log_success "服务部署完成"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    timeout=120
    while [ $timeout -gt 0 ]; do
        backend_status=$(docker-compose ps backend --format "table {{.Status}}" | tail -n 1)
        if [[ "$backend_status" == *"healthy"* ]]; then
            log_success "后端服务启动成功"
            break
        elif [[ "$backend_status" == *"Up"* ]]; then
            # 如果容器运行但还没有健康状态，等待健康检查
            log_info "后端容器运行中，等待健康检查通过..."
        elif [[ "$backend_status" == *"Exit"* ]] || [[ "$backend_status" == *"exited"* ]]; then
            log_error "后端容器启动失败，请检查日志: docker-compose logs backend"
            exit 1
        fi
        sleep 3
        timeout=$((timeout-3))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "后端服务启动超时，最后状态: $backend_status"
        log_error "请检查日志: docker-compose logs backend"
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
    echo "   前后端服务："
    docker-compose ps
    echo ""
    echo "   独立Qdrant数据库："
    docker ps --filter "name=qdrant-standalone" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 管理命令："
    echo "   查看日志: docker-compose logs -f"
    echo "   停止前后端: docker-compose down"
    echo "   停止Qdrant: docker stop qdrant-standalone"
    echo "   停止所有服务: docker-compose down && docker stop qdrant-standalone"
    echo "   重启前后端: docker-compose restart"
    echo "   查看状态: docker-compose ps && docker ps --filter 'name=qdrant-standalone'"
}

# 主函数
main() {
    echo "🚀 开始部署 iHomeMedia..."
    echo ""
    
    check_requirements
    prepare_media_dirs
    deploy_qdrant_standalone $1
    deploy_services $1
    wait_for_services
    show_deployment_info
    
    log_success "部署完成！请使用 http://localhost:3000 访问应用"
}

# 显示帮助信息
show_help() {
    echo "iHomeMedia 部署脚本 (前后端分离 + 独立Qdrant)"
    echo ""
    echo "用法:"
    echo "  $0                 # 正常部署（仅在必要时重建镜像）"
    echo "  $0 --build        # 强制重新构建所有镜像后部署"
    echo "  $0 --clean        # 清理旧镜像和Qdrant数据并重新部署"
    echo "  $0 --fix-dimension # 修复Qdrant向量维度问题（删除旧集合）"
    echo "  $0 --help         # 显示帮助信息"
    echo ""
    echo "部署流程:"
    echo "  1. 检查系统要求和准备媒体目录"
    echo "  2. 独立部署Qdrant向量数据库容器"
    echo "  3. 使用docker-compose部署前后端服务"
    echo "  4. 等待所有服务启动完成"
    echo ""
    echo "说明:"
    echo "  Qdrant数据库使用独立容器运行在localhost:6333"
    echo "  前后端服务通过docker-compose管理"
    echo "  默认模式会让Docker自动判断是否需要重建镜像"
    echo "  使用 --build 参数可以强制重新构建所有镜像"
    echo "  如果遇到向量维度错误，使用 --fix-dimension 修复"
}

# 处理命令行参数
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --build|--clean|--fix-dimension)
        main $1
        ;;
    "")
        main
        ;;
    *)
        log_error "未知参数: $1"
        show_help
        exit 1
        ;;
esac 