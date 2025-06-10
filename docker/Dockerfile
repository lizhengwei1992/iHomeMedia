FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/app /app/app
COPY backend/static /app/static
COPY media /app/media

# 如果前端已构建，复制前端文件
COPY frontend/dist /app/frontend/dist

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=5000

# 创建媒体目录
RUN mkdir -p /app/media/photos /app/media/videos /app/media/thumbnails

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
