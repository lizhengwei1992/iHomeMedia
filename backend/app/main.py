import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import MEDIA_ROOT, PHOTOS_DIR, VIDEOS_DIR, settings
from app.routers import auth, media, search
from app.database.qdrant_manager import init_qdrant

# 创建 FastAPI 应用
app = FastAPI(
    title="家庭照片视频管理服务",
    description="用于家庭照片和视频的上传、存储和浏览",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    try:
        # 初始化Qdrant数据库
        await init_qdrant()
        print("✅ Qdrant数据库初始化成功")
    except Exception as e:
        print(f"❌ Qdrant数据库初始化失败: {str(e)}")
        # 可以选择是否继续启动应用
        # raise e
        
    try:
        # 初始化Embedding服务
        from app.services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        print("✅ Embedding服务初始化成功")
    except Exception as e:
        print(f"❌ Embedding服务初始化失败: {str(e)}")
        print("   请检查DASHSCOPE_API_KEY配置")
        # 可以选择是否继续启动应用
        # raise e

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(media.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)

# 媒体文件静态服务
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

# 缩略图静态文件服务
thumbnails_dir = os.path.join(MEDIA_ROOT, "thumbnails")
if os.path.exists(thumbnails_dir):
    app.mount("/thumbnails", StaticFiles(directory=thumbnails_dir), name="thumbnails")

# 添加app静态文件服务（用于占位图像等）
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/app-static", StaticFiles(directory=static_dir), name="app-static")

# 前端静态文件路径检查
# 尝试几种可能的前端构建目录
frontend_paths = [
    # Docker路径
    "/app/frontend/build",
    # 新的Vite构建路径
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),
    # 相对路径
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "build"),
]

# 查找第一个存在的前端目录
frontend_dir = None
for path in frontend_paths:
    if os.path.exists(path) and os.path.isdir(path):
        frontend_dir = path
        break

# 如果找到前端目录，挂载它
templates = None
if frontend_dir:
    print(f"挂载前端静态文件: {frontend_dir}")
    # 注意：这里的挂载顺序很重要，必须先挂载特定路径，最后挂载根路径
    # 挂载前端静态文件，但不挂载到根路径以避免覆盖API路由
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend-static")
    templates = Jinja2Templates(directory=frontend_dir)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路径，返回前端应用
    """
    if frontend_dir and templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse("""
        <html>
            <head>
                <title>家庭照片视频管理服务</title>
            </head>
            <body>
                <h1>家庭照片视频管理服务 API</h1>
                <p>前端应用尚未构建，请访问 <a href="/docs">/docs</a> 查看 API 文档</p>
                <p>如需前后端分离部署，可使用以下配置:</p>
                <pre>
# Nginx配置示例
server {
    listen 80;
    
    location / {
        root /path/to/frontend/dist;  # 前端构建目录
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
                </pre>
            </body>
        </html>
        """)


@app.get("/ping")
async def ping():
    """
    健康检查接口
    """
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
