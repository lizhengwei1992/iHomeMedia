import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiofiles
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

# 导入HEIF支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

from app.core.config import PHOTOS_DIR, VIDEOS_DIR, settings, MEDIA_ROOT
from app.schemas.media import MediaType
from app.utils.media_processor import create_thumbnail, create_video_thumbnail
from app.utils.description_handler import get_media_description, delete_media_description


def get_media_type(filename: str) -> Optional[MediaType]:
    """
    根据文件扩展名确定媒体类型
    """
    ext = os.path.splitext(filename.lower())[1]
    
    if ext in settings.ALLOWED_PHOTO_EXTENSIONS:
        return MediaType.PHOTO
    elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    
    return None


def get_date_directory(media_type: MediaType) -> Tuple[str, str]:
    """
    获取日期目录路径
    返回: (基本目录, 日期子目录)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    if media_type == MediaType.PHOTO:
        base_dir = PHOTOS_DIR
    elif media_type == MediaType.VIDEO:
        base_dir = VIDEOS_DIR
    else:
        raise ValueError(f"不支持的媒体类型: {media_type}")
    
    date_dir = os.path.join(base_dir, today)
    os.makedirs(date_dir, exist_ok=True)
    
    return base_dir, date_dir


def generate_unique_filename(filename: str) -> str:
    """
    生成唯一文件名，避免冲突
    """
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{name}_{timestamp}{ext}"


def generate_global_media_id(filename: str, upload_time: str) -> str:
    """
    生成全局唯一的32位媒体ID
    基于文件名和上传时间生成
    
    Args:
        filename: 原始文件名
        upload_time: 上传时间（ISO格式字符串）
        
    Returns:
        str: 32位十六进制字符串ID
    """
    import hashlib
    
    # 结合文件名和上传时间生成唯一标识
    unique_string = f"{filename}_{upload_time}"
    
    # 生成MD5哈希并取前32位
    hash_object = hashlib.md5(unique_string.encode())
    return hash_object.hexdigest()[:32]


async def save_upload_file(file: UploadFile, media_type: MediaType) -> Dict:
    """
    保存上传的文件到对应目录
    """
    _, date_dir = get_date_directory(media_type)
    
    # 生成唯一文件名
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(date_dir, unique_filename)
    
    # 保存文件
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # 返回文件信息
    file_size = os.path.getsize(file_path)
    relative_path = os.path.relpath(file_path, MEDIA_ROOT)
    upload_time = datetime.now().isoformat()
    
    # 生成32位全局媒体ID（使用原始文件名和上传时间）
    global_media_id = generate_global_media_id(file.filename, upload_time)
    
    # 构建URL
    original_url = f"/media/{relative_path}"
    
    # 构建缩略图URL
    thumbnail_url = None
    if media_type == MediaType.PHOTO:
        # 对于HEIC文件，缩略图会被转换为JPEG格式
        if file_path.lower().endswith(('.heic', '.heif')):
            thumbnail_rel_path = relative_path.rsplit('.', 1)[0] + '.jpg'
            thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
        else:
            thumbnail_url = f"/thumbnails/{relative_path}"
    elif media_type == MediaType.VIDEO:
        # 视频缩略图使用.jpg扩展名
        thumbnail_rel_path = relative_path.rsplit('.', 1)[0] + '.jpg'
        thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
    
    # 获取图片尺寸（如果是照片）
    width = None
    height = None
    if media_type == MediaType.PHOTO:
        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except UnidentifiedImageError:
            # 无法识别的图像格式，忽略
            pass
    
    return {
        "file_name": unique_filename,
        "file_id": unique_filename,  # 保持兼容性
        "global_media_id": global_media_id,  # 新的32位全局ID
        "original_name": file.filename,
        "file_type": media_type,
        "file_size": file_size,
        "file_path": file_path,
        "relative_path": relative_path,
        "original_url": original_url,
        "thumbnail_url": thumbnail_url,
        "upload_time": upload_time,
        "width": width,
        "height": height
    }


def list_media_files(
    media_type: Optional[MediaType] = None,
    page: int = 1,
    page_size: int = 20,
    date_dir: Optional[str] = None
) -> Dict:
    """
    列出媒体文件
    """
    items = []
    base_dirs = []
    
    # 确定要搜索的基本目录
    if media_type == MediaType.PHOTO:
        base_dirs = [PHOTOS_DIR]
    elif media_type == MediaType.VIDEO:
        base_dirs = [VIDEOS_DIR]
    else:
        base_dirs = [PHOTOS_DIR, VIDEOS_DIR]
    
    all_files = []
    
    # 遍历目录收集文件
    for base_dir in base_dirs:
        if date_dir:
            # 如果指定了日期目录，只搜索该目录
            target_dir = os.path.join(base_dir, date_dir)
            if os.path.exists(target_dir):
                for file in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, file)
                    if os.path.isfile(file_path):
                        all_files.append(file_path)
        else:
            # 否则搜索所有日期目录
            for root, _, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
    
    # 按修改时间排序（最新的在前）
    all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    files_page = all_files[start_idx:end_idx]
    
    # 构建媒体项目列表
    for file_path in files_page:
        file_name = os.path.basename(file_path)
        media_type = get_media_type(file_name)
        
        if not media_type:
            continue  # 跳过不支持的文件类型
        
        file_size = os.path.getsize(file_path)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 构建访问URL（相对路径）
        rel_path = os.path.relpath(file_path, MEDIA_ROOT)
        url = f"/media/{rel_path}"
        
        # 缩略图URL
        thumbnail_url = None
        if media_type == MediaType.PHOTO:
            # 对于HEIC文件，缩略图会被转换为JPEG格式
            if file_path.lower().endswith(('.heic', '.heif')):
                # HEIC缩略图使用.jpg扩展名
                thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
                thumbnail_path = os.path.join(MEDIA_ROOT, "thumbnails", thumbnail_rel_path)
                thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
            else:
                # 其他格式使用原扩展名
                thumbnail_path = os.path.join(MEDIA_ROOT, "thumbnails", rel_path)
                thumbnail_url = f"/thumbnails/{rel_path}"
            
            # 如果缩略图不存在则创建
            if not os.path.exists(thumbnail_path):
                try:
                    create_thumbnail(file_path)
                except Exception as e:
                    print(f"创建缩略图出错: {e}")
                    # 创建失败时使用原图
                    thumbnail_url = url
            
        elif media_type == MediaType.VIDEO:
            # 视频缩略图使用.jpg扩展名
            thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
            thumbnail_path = os.path.join(MEDIA_ROOT, "thumbnails", thumbnail_rel_path)
            thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
            
            # 如果缩略图不存在则创建
            if not os.path.exists(thumbnail_path):
                try:
                    create_video_thumbnail(file_path)
                except Exception as e:
                    print(f"创建视频缩略图出错: {e}")
                    # 创建失败时使用默认占位图
                    thumbnail_url = "/app-static/video-thumbnail.png"
        
        # 图片尺寸（如果是照片）
        width = None
        height = None
        duration = None
        
        if media_type == MediaType.PHOTO:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception:
                # 忽略无法处理的图片
                pass
        
        # 获取媒体描述
        description = get_media_description(file_name)
        
        item = {
            "id": file_name,
            "name": file_name,
            "type": media_type,
            "path": rel_path,
            "size": file_size,
            "url": url,
            "thumbnail_url": thumbnail_url,
            "upload_date": file_mtime,
            "width": width,
            "height": height,
            "duration": duration,
            "description": description
        }
        
        items.append(item)
    
    return {
        "items": items,
        "total": len(all_files),
        "page": page,
        "page_size": page_size
    }


def delete_media_file(file_id: str) -> bool:
    """
    删除媒体文件和对应的缩略图
    """
    try:
        # 查找文件
        all_files = []
        base_dirs = [PHOTOS_DIR, VIDEOS_DIR]
        
        for base_dir in base_dirs:
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file == file_id:
                        file_path = os.path.join(root, file)
                        all_files.append(file_path)
        
        if not all_files:
            print(f"文件未找到: {file_id}")
            raise FileNotFoundError(f"文件未找到: {file_id}")
        
        # 通常应该只有一个文件，但以防万一
        for file_path in all_files:
            # 删除原文件
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"删除原文件: {file_path}")
            
            # 删除对应的缩略图
            rel_path = os.path.relpath(file_path, MEDIA_ROOT)
            
            # 对于HEIC和视频文件，缩略图是.jpg格式
            if file_path.lower().endswith(('.heic', '.heif')) or get_media_type(file_path) == MediaType.VIDEO:
                thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
            else:
                thumbnail_rel_path = rel_path
            
            thumbnail_path = os.path.join(MEDIA_ROOT, "thumbnails", thumbnail_rel_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                print(f"删除缩略图: {thumbnail_path}")
        
        # 删除媒体描述
        delete_media_description(file_id)
        
        return True
        
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False


def find_media_file_by_id(file_id: str) -> Optional[Dict]:
    """
    根据文件ID查找媒体文件信息
    
    Args:
        file_id: 文件ID（文件名）
        
    Returns:
        Dict: 文件信息字典，如果未找到返回None
    """
    try:
        # 查找文件
        base_dirs = [PHOTOS_DIR, VIDEOS_DIR]
        
        for base_dir in base_dirs:
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file == file_id:
                        file_path = os.path.join(root, file)
                        
                        # 获取文件信息
                        file_size = os.path.getsize(file_path)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        media_type = get_media_type(file)
                        
                        # 构建相对路径和URL
                        rel_path = os.path.relpath(file_path, MEDIA_ROOT)
                        url = f"/media/{rel_path}"
                        
                        # 缩略图URL
                        thumbnail_url = None
                        if media_type == MediaType.PHOTO:
                            if file_path.lower().endswith(('.heic', '.heif')):
                                thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
                                thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
                            else:
                                thumbnail_url = f"/thumbnails/{rel_path}"
                        elif media_type == MediaType.VIDEO:
                            thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
                            thumbnail_url = f"/thumbnails/{thumbnail_rel_path}"
                        
                        # 获取描述
                        description = get_media_description(file_id)
                        
                        return {
                            "id": file_id,
                            "name": file,
                            "type": media_type,
                            "path": rel_path,
                            "size": file_size,
                            "url": url,
                            "thumbnail_url": thumbnail_url,
                            "upload_date": file_mtime.isoformat(),
                            "description": description
                        }
        
        return None
        
    except Exception as e:
        print(f"查找文件失败 {file_id}: {str(e)}")
        return None
