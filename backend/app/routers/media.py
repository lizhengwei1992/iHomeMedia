from typing import Any, List, Optional
import logging
import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.core.security import get_current_user
from app.schemas.media import MediaList, MediaType, UploadResult
from app.utils.file_handler import get_media_type, list_media_files, save_upload_file, delete_media_file
from app.utils.media_processor import create_thumbnail, create_video_thumbnail
from app.utils.description_handler import set_media_description
from app.services.vector_storage_service import get_vector_storage_service

router = APIRouter(prefix="/media", tags=["媒体文件"])


@router.post("/upload", response_model=List[UploadResult])
async def upload_media_files(
    files: List[UploadFile] = File(...),
    descriptions: Optional[List[str]] = Form(None),
    auto_generate_embeddings: bool = Form(True),
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    上传媒体文件（照片或视频）
    增强版本：支持自动生成embeddings并存储到向量数据库
    考虑速率限制，在批量上传时添加适当间隔
    """
    results = []
    vector_service = get_vector_storage_service()
    
    # 处理描述列表，确保与文件数量匹配
    if descriptions is None:
        descriptions = [""] * len(files)
    elif len(descriptions) < len(files):
        descriptions.extend([""] * (len(files) - len(descriptions)))
    
    logger.info(f"开始上传 {len(files)} 个媒体文件，自动生成embedding: {auto_generate_embeddings}")
    
    for i, file in enumerate(files):
        # 如果不是第一个文件且需要生成embedding，添加小间隔避免速率限制
        if i > 0 and auto_generate_embeddings:
            logger.info(f"等待1秒后处理下一个文件，避免速率限制...")
            await asyncio.sleep(1.0)
        
        logger.info(f"处理文件 {i + 1}/{len(files)}: {file.filename}")
        
        # 检查文件类型
        media_type = get_media_type(file.filename)
        if not media_type:
            results.append({
                "success": False,
                "file_name": file.filename,
                "file_type": None,
                "file_size": 0,
                "file_path": "",
                "message": "不支持的文件类型",
                "embedding_generated": False
            })
            continue
        
        # 保存文件
        try:
            file_info = await save_upload_file(file, media_type)
            file_id = file_info.get("file_id")
            global_media_id = file_info.get("global_media_id")  # 新的32位全局ID
            description = descriptions[i] if i < len(descriptions) else ""
            
            # 创建缩略图
            thumbnail_created = False
            if media_type == MediaType.PHOTO:
                try:
                    create_thumbnail(file_info["file_path"])
                    thumbnail_created = True
                    logger.info(f"成功创建缩略图: {file_info['file_path']}")
                except Exception as e:
                    logger.warning(f"创建照片缩略图失败: {str(e)}")
                    # 继续处理，不中断上传流程
            elif media_type == MediaType.VIDEO:
                try:
                    create_video_thumbnail(file_info["file_path"])
                    thumbnail_created = True
                    logger.info(f"成功创建视频缩略图: {file_info['file_path']}")
                except Exception as e:
                    logger.warning(f"创建视频缩略图失败: {str(e)}")
                    # 继续处理，不中断上传流程
            
            # 保存描述到JSON文件（兼容现有系统）
            if description:
                try:
                    set_media_description(file_id, description)
                except Exception as e:
                    logger.warning(f"保存描述到JSON失败: {str(e)}")
            
            # 生成embedding并存储到向量数据库
            embedding_generated = False
            embedding_error = None
            
            # 确保global_media_id不为None
            if not global_media_id:
                logger.error("global_media_id为空，无法生成embedding")
                embedding_error = "全局媒体ID为空"
            elif auto_generate_embeddings:
                try:
                    logger.info(f"开始为文件 {global_media_id} 生成embedding...")
                    embedding_result = await vector_service.store_media_embedding(
                        media_id=global_media_id,  # 使用32位全局ID
                        file_path=file_info["file_path"],
                        file_type=media_type.value,
                        file_size=file_info["file_size"],
                        upload_time=file_info["upload_time"],  # 使用精确的上传时间
                        description=description,
                        force_regenerate=False,
                        # 传递额外的元数据
                        extra_metadata={
                            "original_name": file_info["original_name"],
                            "file_id": file_id,  # 保持兼容性
                            "original_url": file_info["original_url"],
                            "thumbnail_url": file_info["thumbnail_url"],
                            "relative_path": file_info["relative_path"],
                            "width": file_info.get("width"),
                            "height": file_info.get("height")
                        }
                    )
                    
                    if embedding_result.success:
                        embedding_generated = True
                        logger.info(f"媒体文件 {global_media_id} embedding生成成功 "
                                  f"(文本: {embedding_result.text_embedding_generated}, "
                                  f"图像: {embedding_result.image_embedding_generated})")
                    else:
                        embedding_error = embedding_result.error_message
                        logger.warning(f"媒体文件 {global_media_id} embedding生成失败: {embedding_error}")
                        
                except Exception as e:
                    embedding_error = str(e)
                    logger.error(f"生成embedding异常: {str(e)}")
            
            # 构建成功结果
            upload_result = {
                "success": True,
                "file_name": file_info["file_name"],
                "file_type": media_type,
                "file_size": file_info["file_size"],
                "file_path": file_info["relative_path"],
                "file_id": file_id,
                "global_media_id": global_media_id,  # 返回32位全局ID
                "original_url": file_info["original_url"],
                "thumbnail_url": file_info["thumbnail_url"],
                "thumbnail_created": thumbnail_created,
                "embedding_generated": embedding_generated,
                "description": description,
                "message": "上传成功"
            }
            
            if embedding_error:
                upload_result["embedding_error"] = embedding_error
            
            results.append(upload_result)
        
        except Exception as e:
            logger.error(f"上传文件失败 {file.filename}: {str(e)}")
            results.append({
                "success": False,
                "file_name": file.filename,
                "file_type": media_type,
                "file_size": 0,
                "file_path": "",
                "file_id": None,
                "thumbnail_created": False,
                "embedding_generated": False,
                "message": f"上传失败: {str(e)}"
            })
    
    successful_uploads = sum(1 for r in results if r.get("success", False))
    successful_embeddings = sum(1 for r in results if r.get("embedding_generated", False))
    
    logger.info(f"批量上传完成: {successful_uploads}/{len(files)} 上传成功, "
               f"{successful_embeddings}/{len(files)} embedding生成成功")
    
    return results


@router.get("/list", response_model=MediaList)
async def get_media_files(
    media_type: Optional[MediaType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_dir: Optional[str] = None,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取媒体文件列表
    """
    result = list_media_files(
        media_type=media_type,
        page=page,
        page_size=page_size,
        date_dir=date_dir
    )
    
    return result


@router.get("/dates")
async def get_available_dates(
    media_type: Optional[MediaType] = None,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取可用的日期目录
    """
    # 实现日期目录列表
    pass


@router.delete("/{file_id}")
async def delete_media_file_endpoint(
    file_id: str,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    删除媒体文件
    """
    try:
        success = delete_media_file(file_id)
        if success:
            return {"success": True, "message": "文件删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.put("/{file_id}/description")
async def update_media_description(
    file_id: str,
    description: str = Form(...),
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    更新媒体文件描述
    """
    try:
        success = set_media_description(file_id, description)
        if success:
            return {"success": True, "message": "描述更新成功"}
        else:
            raise HTTPException(status_code=500, detail="描述更新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
