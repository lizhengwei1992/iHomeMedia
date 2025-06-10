from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

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
    file_id: Optional[str] = None  # 文件ID
    global_media_id: Optional[str] = None  # 32位全局媒体ID
    original_url: Optional[str] = None  # 原文件URL
    thumbnail_url: Optional[str] = None  # 缩略图URL
    thumbnail_created: Optional[bool] = None  # 是否创建了缩略图
    embedding_generated: Optional[Union[bool, str]] = None  # embedding是否生成或状态
    embedding_task_id: Optional[str] = None  # embedding任务ID
    description: Optional[str] = None  # 文件描述
    message: Optional[str] = None  # 响应消息
