from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class MediaType(str, Enum):
    """
    媒体类型枚举
    """
    PHOTO = "photo"
    VIDEO = "video"


class MediaItem(BaseModel):
    """
    媒体项目模型
    """
    id: str  # 文件名作为ID
    name: str
    type: MediaType
    path: str
    size: int  # 文件大小（字节）
    url: str  # 访问URL
    thumbnail_url: Optional[str] = None  # 缩略图URL（仅对照片和视频有效）
    upload_date: datetime
    width: Optional[int] = None  # 宽度（像素）
    height: Optional[int] = None  # 高度（像素）
    duration: Optional[float] = None  # 视频时长（秒）
    description: Optional[str] = None  # 媒体内容说明


class MediaList(BaseModel):
    """
    媒体列表响应模型
    """
    items: List[MediaItem]
    total: int
    page: int
    page_size: int


class UploadResult(BaseModel):
    """
    上传结果响应模型
    """
    success: bool
    file_name: str
    file_type: MediaType
    file_size: int
    file_path: str
    message: Optional[str] = None
