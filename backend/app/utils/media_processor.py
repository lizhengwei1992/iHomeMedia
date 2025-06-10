import os
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

# 导入HEIF支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

from app.core.config import PHOTOS_DIR, MEDIA_ROOT, settings


def create_thumbnail(file_path: str) -> str:
    """
    为图像创建缩略图
    """
    try:
        # 确保缩略图目录存在
        thumbnail_dir = os.path.join(MEDIA_ROOT, "thumbnails")
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        # 获取相对路径
        rel_path = os.path.relpath(file_path, MEDIA_ROOT)
        
        # 构建缩略图路径
        thumbnail_path = os.path.join(thumbnail_dir, rel_path)
        
        # 确保缩略图目录存在
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        # 打开图片并创建缩略图
        with Image.open(file_path) as img:
            # 保持纵横比创建缩略图
            img.thumbnail(settings.THUMBNAIL_SIZE)
            
            # 如果原图是HEIC格式，将缩略图保存为JPEG格式以便浏览器显示
            if file_path.lower().endswith(('.heic', '.heif')):
                # 将HEIC缩略图保存为JPEG格式
                thumbnail_path = thumbnail_path.rsplit('.', 1)[0] + '.jpg'
                # 转换为RGB模式（JPEG不支持透明度）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(thumbnail_path, 'JPEG', quality=85)
                print(f"成功创建HEIC缩略图(转换为JPEG): {thumbnail_path}")
            else:
                # 其他格式正常保存
                img.save(thumbnail_path, quality=85)
                print(f"成功创建缩略图: {thumbnail_path}")
        
        return thumbnail_path
        
    except (UnidentifiedImageError, Exception) as e:
        print(f"创建缩略图失败: {str(e)}")
        return ""


def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """
    获取图片尺寸
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except (UnidentifiedImageError, OSError, IOError):
        return None


def create_video_thumbnail(file_path: str) -> str:
    """
    为视频创建缩略图（提取第一帧）
    """
    try:
        # 确保缩略图目录存在
        thumbnail_dir = os.path.join(MEDIA_ROOT, "thumbnails")
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        # 获取相对路径
        rel_path = os.path.relpath(file_path, MEDIA_ROOT)
        
        # 构建缩略图路径，将视频扩展名改为.jpg
        thumbnail_rel_path = rel_path.rsplit('.', 1)[0] + '.jpg'
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_rel_path)
        
        # 确保缩略图目录存在
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        # 使用OpenCV读取视频第一帧
        cap = cv2.VideoCapture(file_path)
        
        if not cap.isOpened():
            print(f"无法打开视频文件: {file_path}")
            return ""
        
        # 读取第一帧
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print(f"无法读取视频第一帧: {file_path}")
            return ""
        
        # 将OpenCV的BGR格式转换为PIL的RGB格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 转换为PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # 创建缩略图
        pil_image.thumbnail(settings.THUMBNAIL_SIZE)
        
        # 保存为JPEG格式
        pil_image.save(thumbnail_path, 'JPEG', quality=85)
        
        print(f"成功创建视频缩略图: {thumbnail_path}")
        
        return thumbnail_path
        
    except Exception as e:
        print(f"创建视频缩略图失败: {str(e)}")
        return ""


def is_valid_image(file_content: bytes) -> bool:
    """
    验证文件是否为有效图片
    """
    try:
        Image.open(BytesIO(file_content))
        return True
    except (UnidentifiedImageError, OSError, IOError):
        return False
