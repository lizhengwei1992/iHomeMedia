#!/bin/bash

# 家庭媒体应用停止脚本
echo "=========================================="
echo "  家庭媒体应用停止脚本"
echo "=========================================="

# 项目根目录
cd "$(dirname "$0")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示当前运行的服务
echo -e "${BLUE}📋 当前运行的相关服务:${NC}"
echo "----------------------------------------"

# 检查后端服务 (uvicorn)
BACKEND_PIDS=$(ps aux | grep -E "uvicorn.*app\.main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}🔧 后端服务 (uvicorn):${NC}"
    ps aux | grep -E "uvicorn.*app\.main:app" | grep -v grep | while read line; do
        echo "  $line"
    done
else
    echo -e "${GREEN}✅ 后端服务: 未运行${NC}"
fi

# 检查前端代理服务 (python server.py)
FRONTEND_PIDS=$(ps aux | grep -E "python.*server\.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}🌐 前端代理服务:${NC}"
    ps aux | grep -E "python.*server\.py" | grep -v grep | while read line; do
        echo "  $line"
    done
else
    echo -e "${GREEN}✅ 前端代理服务: 未运行${NC}"
fi

# 检查Node.js/Vite服务
NODE_PIDS=$(ps aux | grep -E "(node.*vite|npm.*dev)" | grep -v grep | awk '{print $2}')
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${YELLOW}⚡ Node.js/Vite服务:${NC}"
    ps aux | grep -E "(node.*vite|npm.*dev)" | grep -v grep | while read line; do
        echo "  $line"
    done
else
    echo -e "${GREEN}✅ Node.js/Vite服务: 未运行${NC}"
fi

# 检查端口占用
echo -e "\n${BLUE}🔍 端口占用情况:${NC}"
echo "----------------------------------------"
PORT_3000=$(lsof -ti:3000 2>/dev/null)
PORT_5000=$(lsof -ti:5000 2>/dev/null)

if [ ! -z "$PORT_3000" ]; then
    echo -e "${YELLOW}端口 3000:${NC}"
    lsof -i:3000 | tail -n +2 | while read line; do
        echo "  $line"
    done
else
    echo -e "${GREEN}✅ 端口 3000: 空闲${NC}"
fi

if [ ! -z "$PORT_5000" ]; then
    echo -e "${YELLOW}端口 5000:${NC}"
    lsof -i:5000 | tail -n +2 | while read line; do
        echo "  $line"
    done
else
    echo -e "${GREEN}✅ 端口 5000: 空闲${NC}"
fi

# 如果没有任何服务运行，直接退出
if [ -z "$BACKEND_PIDS" ] && [ -z "$FRONTEND_PIDS" ] && [ -z "$NODE_PIDS" ] && [ -z "$PORT_3000" ] && [ -z "$PORT_5000" ]; then
    echo -e "\n${GREEN}🎉 没有发现运行中的服务，无需停止${NC}"
    exit 0
fi

# 询问用户是否要停止服务
echo -e "\n${BLUE}请选择操作:${NC}"
echo "1) 优雅停止所有服务 (推荐)"
echo "2) 强制停止所有服务"
echo "3) 仅停止后端服务"
echo "4) 仅停止前端服务"
echo "5) 清理占用端口的所有进程"
echo "6) 取消操作"
read -p "请输入选项 [1]: " choice

# 默认选择1
choice=${choice:-1}

case $choice in
  1)
    echo -e "\n${BLUE}🛑 优雅停止所有服务...${NC}"
    
    # 优雅停止后端服务
    if [ ! -z "$BACKEND_PIDS" ]; then
        echo -e "${YELLOW}停止后端服务...${NC}"
        for pid in $BACKEND_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已发送停止信号给后端进程 $pid"
        done
        sleep 2
        
        # 检查是否还在运行
        for pid in $BACKEND_PIDS; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "  ${RED}⚠️  进程 $pid 未响应，强制停止${NC}"
                kill -KILL $pid 2>/dev/null
            fi
        done
    fi
    
    # 优雅停止前端服务
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo -e "${YELLOW}停止前端代理服务...${NC}"
        for pid in $FRONTEND_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已发送停止信号给前端进程 $pid"
        done
        sleep 1
    fi
    
    # 优雅停止Node.js服务
    if [ ! -z "$NODE_PIDS" ]; then
        echo -e "${YELLOW}停止Node.js/Vite服务...${NC}"
        for pid in $NODE_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已发送停止信号给Node.js进程 $pid"
        done
        sleep 1
    fi
    ;;
    
  2)
    echo -e "\n${RED}💀 强制停止所有服务...${NC}"
    
    # 强制停止所有相关进程
    if [ ! -z "$BACKEND_PIDS" ]; then
        echo -e "${YELLOW}强制停止后端服务...${NC}"
        for pid in $BACKEND_PIDS; do
            kill -KILL $pid 2>/dev/null && echo "  ✅ 强制停止后端进程 $pid"
        done
    fi
    
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo -e "${YELLOW}强制停止前端代理服务...${NC}"
        for pid in $FRONTEND_PIDS; do
            kill -KILL $pid 2>/dev/null && echo "  ✅ 强制停止前端进程 $pid"
        done
    fi
    
    if [ ! -z "$NODE_PIDS" ]; then
        echo -e "${YELLOW}强制停止Node.js/Vite服务...${NC}"
        for pid in $NODE_PIDS; do
            kill -KILL $pid 2>/dev/null && echo "  ✅ 强制停止Node.js进程 $pid"
        done
    fi
    ;;
    
  3)
    echo -e "\n${BLUE}🛑 仅停止后端服务...${NC}"
    if [ ! -z "$BACKEND_PIDS" ]; then
        for pid in $BACKEND_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已停止后端进程 $pid"
        done
    else
        echo -e "${GREEN}✅ 后端服务未运行${NC}"
    fi
    ;;
    
  4)
    echo -e "\n${BLUE}🛑 仅停止前端服务...${NC}"
    if [ ! -z "$FRONTEND_PIDS" ]; then
        for pid in $FRONTEND_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已停止前端进程 $pid"
        done
    fi
    if [ ! -z "$NODE_PIDS" ]; then
        for pid in $NODE_PIDS; do
            kill -TERM $pid 2>/dev/null && echo "  ✅ 已停止Node.js进程 $pid"
        done
    fi
    if [ -z "$FRONTEND_PIDS" ] && [ -z "$NODE_PIDS" ]; then
        echo -e "${GREEN}✅ 前端服务未运行${NC}"
    fi
    ;;
    
  5)
    echo -e "\n${RED}🧹 清理占用端口的所有进程...${NC}"
    
    # 清理3000端口
    if [ ! -z "$PORT_3000" ]; then
        echo -e "${YELLOW}清理端口3000...${NC}"
        lsof -ti:3000 | xargs kill -KILL 2>/dev/null && echo "  ✅ 已清理端口3000"
    fi
    
    # 清理5000端口
    if [ ! -z "$PORT_5000" ]; then
        echo -e "${YELLOW}清理端口5000...${NC}"
        lsof -ti:5000 | xargs kill -KILL 2>/dev/null && echo "  ✅ 已清理端口5000"
    fi
    ;;
    
  6)
    echo -e "\n${GREEN}✅ 已取消操作${NC}"
    exit 0
    ;;
    
  *)
    echo -e "\n${RED}❌ 无效选项: $choice${NC}"
    exit 1
    ;;
esac

# 等待进程完全停止
echo -e "\n${BLUE}⏳ 等待进程完全停止...${NC}"
sleep 3

# 显示停止后的状态
echo -e "\n${BLUE}📋 停止后的服务状态:${NC}"
echo "----------------------------------------"

# 再次检查后端服务
REMAINING_BACKEND=$(ps aux | grep -E "uvicorn.*app\.main:app" | grep -v grep)
if [ -z "$REMAINING_BACKEND" ]; then
    echo -e "${GREEN}✅ 后端服务: 已停止${NC}"
else
    echo -e "${RED}❌ 后端服务: 仍在运行${NC}"
    echo "$REMAINING_BACKEND"
fi

# 再次检查前端服务
REMAINING_FRONTEND=$(ps aux | grep -E "python.*server\.py" | grep -v grep)
if [ -z "$REMAINING_FRONTEND" ]; then
    echo -e "${GREEN}✅ 前端代理服务: 已停止${NC}"
else
    echo -e "${RED}❌ 前端代理服务: 仍在运行${NC}"
    echo "$REMAINING_FRONTEND"
fi

# 再次检查Node.js服务
REMAINING_NODE=$(ps aux | grep -E "(node.*vite|npm.*dev)" | grep -v grep)
if [ -z "$REMAINING_NODE" ]; then
    echo -e "${GREEN}✅ Node.js/Vite服务: 已停止${NC}"
else
    echo -e "${RED}❌ Node.js/Vite服务: 仍在运行${NC}"
    echo "$REMAINING_NODE"
fi

# 再次检查端口
echo -e "\n${BLUE}🔍 端口状态:${NC}"
FINAL_3000=$(lsof -ti:3000 2>/dev/null)
FINAL_5000=$(lsof -ti:5000 2>/dev/null)

if [ -z "$FINAL_3000" ]; then
    echo -e "${GREEN}✅ 端口 3000: 空闲${NC}"
else
    echo -e "${RED}❌ 端口 3000: 仍被占用${NC}"
fi

if [ -z "$FINAL_5000" ]; then
    echo -e "${GREEN}✅ 端口 5000: 空闲${NC}"
else
    echo -e "${RED}❌ 端口 5000: 仍被占用${NC}"
fi

# 提供启动建议
if [ -z "$REMAINING_BACKEND" ] && [ -z "$REMAINING_FRONTEND" ] && [ -z "$REMAINING_NODE" ]; then
    echo -e "\n${GREEN}🎉 所有服务已成功停止！${NC}"
    echo -e "${BLUE}💡 提示: 现在可以运行 './start-app.sh' 重新启动服务${NC}"
else
    echo -e "\n${YELLOW}⚠️  部分服务可能未完全停止，建议检查后再启动新服务${NC}"
    echo -e "${BLUE}💡 如需强制清理，可以重新运行此脚本并选择选项2或5${NC}"
fi

echo -e "\n${BLUE}=========================================="
echo "  停止脚本执行完成"
echo -e "==========================================${NC}" 