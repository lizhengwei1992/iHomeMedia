import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 加载环境变量文件 (优先级: .local.env > .env)
# .local.env 用于本地敏感配置，不提交到Git
local_env_path = ROOT_DIR / ".local.env"
env_path = ROOT_DIR / ".env"

if local_env_path.exists():
    print(f"加载本地环境变量: {local_env_path}")
    load_dotenv(local_env_path)
elif env_path.exists():
    print(f"加载环境变量: {env_path}")
    load_dotenv(env_path)
else:
    print("未找到环境变量文件，使用默认配置")

# 媒体文件存储目录 - 支持从环境变量读取
MEDIA_ROOT = os.environ.get("MEDIA_DIR", os.path.join(ROOT_DIR, "media"))
PHOTOS_DIR = os.path.join(MEDIA_ROOT, "photos")
VIDEOS_DIR = os.path.join(MEDIA_ROOT, "videos")

# 确保媒体目录存在
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)


class Settings(BaseSettings):
    # API 配置
    API_V1_STR: str = "/api/v1"
    
    # 阿里云DashScope配置
    DASHSCOPE_API_KEY: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-for-jwt-token"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 用户认证配置
    DEFAULT_USER: str = "family"
    DEFAULT_PASSWORD: str = "123456"
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_PHOTO_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".mov", ".hevc", ".avi"]
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # 生产环境应限制为具体域名
    
    # 缩略图配置
    THUMBNAIL_SIZE: tuple = (300, 300)
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # 开发配置
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Qdrant配置 (可选)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    # 搜索配置
    # 文本搜索时的两路召回阈值
    TEXT_TO_TEXT_THRESHOLD: float = float(os.environ.get("TEXT_TO_TEXT_THRESHOLD", "0.8"))  # 文本搜媒体描述的阈值
    TEXT_TO_IMAGE_THRESHOLD: float = float(os.environ.get("TEXT_TO_IMAGE_THRESHOLD", "0.1"))  # 文本搜图像的阈值
    
    # 图像搜索的阈值
    IMAGE_SEARCH_THRESHOLD: float = float(os.environ.get("IMAGE_SEARCH_THRESHOLD", "0.5"))  # 图搜图的阈值

    class Config:
        # 支持多个env文件，优先级从高到低
        env_file = [".local.env", ".env"]
        env_file_encoding = "utf-8"


settings = Settings()
