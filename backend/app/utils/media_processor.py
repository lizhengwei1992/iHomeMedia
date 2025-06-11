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
        
        # 特殊处理HEIC文件
        if file_path.lower().endswith(('.heic', '.heif')):
            return create_heic_thumbnail(file_path, thumbnail_path)
        
        # 处理其他格式的图片
        with Image.open(file_path) as img:
            # 其他格式正常处理
            img_copy = img.copy()
            
            # 创建缩略图（兼容不同版本的Pillow）
            try:
                img_copy.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            except AttributeError:
                # 兼容旧版本Pillow
                img_copy.thumbnail(settings.THUMBNAIL_SIZE, Image.LANCZOS)
            
            # 转换模式以兼容保存格式
            if img_copy.mode in ('RGBA', 'LA', 'P'):
                img_copy = img_copy.convert('RGB')
            
            # 保存缩略图
            img_copy.save(thumbnail_path, quality=85)
            print(f"成功创建缩略图: {thumbnail_path}")
        
        return thumbnail_path
        
    except (UnidentifiedImageError, Exception) as e:
        print(f"创建缩略图失败: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return ""


def create_heic_thumbnail(file_path: str, thumbnail_path: str) -> str:
    """
    专门处理HEIC文件的缩略图创建
    """
    try:
        # HEIC缩略图保存为JPEG格式
        jpeg_thumbnail_path = thumbnail_path.rsplit('.', 1)[0] + '.jpg'
        
        # 尝试使用pillow_heif处理
        if HEIF_SUPPORTED:
            try:
                with Image.open(file_path) as img:
                    # 创建图像副本，避免修改原始图像的只读属性
                    img_copy = img.copy()
                    
                    # 如果需要转换模式，先转换
                    if img_copy.mode in ('RGBA', 'LA', 'P'):
                        img_copy = img_copy.convert('RGB')
                    elif img_copy.mode not in ('RGB', 'L'):
                        # 确保模式兼容
                        img_copy = img_copy.convert('RGB')
                    
                    # 创建缩略图（兼容不同版本的Pillow）
                    try:
                        img_copy.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    except AttributeError:
                        # 兼容旧版本Pillow
                        img_copy.thumbnail(settings.THUMBNAIL_SIZE, Image.LANCZOS)
                    
                    # 保存为JPEG格式
                    img_copy.save(jpeg_thumbnail_path, 'JPEG', quality=85)
                    print(f"成功创建HEIC缩略图(转换为JPEG): {jpeg_thumbnail_path}")
                    return jpeg_thumbnail_path
                    
            except Exception as heif_error:
                print(f"pillow_heif处理失败: {str(heif_error)}")
                # 继续尝试使用其他方法
        
        # 如果pillow_heif失败或不可用，尝试使用其他方法
        print("尝试使用替代方法处理HEIC文件...")
        
        # 方法1：尝试用opencv读取（某些HEIC文件可能被opencv支持）
        try:
            import cv2
            img_array = cv2.imread(file_path, cv2.IMREAD_COLOR)
            if img_array is not None:
                # 转换BGR to RGB
                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(img_rgb)
                
                # 创建缩略图
                try:
                    pil_image.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                except AttributeError:
                    pil_image.thumbnail(settings.THUMBNAIL_SIZE, Image.LANCZOS)
                
                pil_image.save(jpeg_thumbnail_path, 'JPEG', quality=85)
                print(f"使用OpenCV成功创建HEIC缩略图: {jpeg_thumbnail_path}")
                return jpeg_thumbnail_path
                
        except Exception as cv_error:
            print(f"OpenCV处理HEIC失败: {str(cv_error)}")
        
        # 如果所有方法都失败，返回空字符串
        print(f"无法为HEIC文件创建缩略图: {file_path}")
        return ""
        
    except Exception as e:
        print(f"HEIC缩略图创建失败: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
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
