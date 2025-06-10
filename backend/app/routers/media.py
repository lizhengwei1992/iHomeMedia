from typing import Any, List, Optional
import logging
import asyncio
import re
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.core.security import get_current_user
from app.schemas.media import MediaList, MediaType, UploadResult
from app.utils.file_handler import get_media_type, list_media_files, save_upload_file, delete_media_file, delete_media_file_async
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
            
            # 添加后台embedding生成任务（无论描述是否为空都要创建）
            task_id = None
            embedding_generated = False
            
            # 确保global_media_id不为None
            if not global_media_id:
                logger.error("global_media_id为空，无法生成embedding")
            elif auto_generate_embeddings:
                try:
                    # 使用任务管理器添加后台任务
                    from app.services.task_manager import get_task_manager
                    task_manager = get_task_manager()
                    
                    # 计算实际的缩略图文件路径（绝对路径）
                    from app.core.config import MEDIA_ROOT
                    import os
                    
                    if file_info["thumbnail_url"]:
                        # 从URL转换为实际文件路径
                        # thumbnail_url格式: "/thumbnails/photos/2025-06-10/IMG_4638_20250610162906.jpeg"
                        thumbnail_rel_path = file_info["thumbnail_url"].replace("/thumbnails/", "")
                        thumbnail_abs_path = os.path.join(MEDIA_ROOT, "thumbnails", thumbnail_rel_path)
                    else:
                        thumbnail_abs_path = file_info["file_path"]  # 如果没有缩略图，使用原文件
                    
                    # 添加embedding生成任务到后台队列，让后台任务创建完整记录
                    # 注意：即使描述为空，也要创建任务，确保向量记录被创建
                    task_id = task_manager.add_upload_embedding_task(
                        file_path=file_info["file_path"],
                        thumbnail_path=thumbnail_abs_path,  # 使用绝对路径
                        description=description or '',  # 即使为空也传递空字符串
                        extra_metadata={
                            "file_name": file_info["file_name"],
                            "file_type": media_type.value,
                            "file_size": file_info["file_size"],
                            "upload_time": file_info["upload_time"],
                            "original_name": file_info["original_name"],
                            "file_id": file_id,
                            "original_url": file_info["original_url"],
                            "thumbnail_url": file_info["thumbnail_url"],
                            "relative_path": file_info["relative_path"],
                            "width": file_info.get("width"),
                            "height": file_info.get("height"),
                            "global_media_id": global_media_id,  # 传递全局ID
                            "force_regenerate": False  # 不强制重新生成，创建新记录
                        }
                    )
                    
                    logger.info(f"已添加embedding生成任务: {task_id} (文件: {global_media_id}, 缩略图: {thumbnail_abs_path})")
                    embedding_generated = "queued"  # 标记为队列中
                        
                except Exception as e:
                    logger.error(f"添加embedding任务失败: {str(e)}")
            
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
                "message": "上传成功" if embedding_generated != "queued" else "上传成功，embedding正在后台生成中"
            }
            
            if task_id:
                upload_result["embedding_task_id"] = task_id
            
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
    删除媒体文件和所有相关数据
    包括：原文件、缩略图、描述文件、向量数据库embedding记录
    """
    try:
        # 使用改进的异步删除函数
        success = await delete_media_file_async(file_id)
        if success:
            return {
                "success": True, 
                "message": "文件及所有相关数据删除成功",
                "deleted_items": [
                    "原文件",
                    "缩略图",
                    "描述文件", 
                    "embedding记录"
                ]
            }
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except FileNotFoundError:
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
        # 立即更新本地描述文件
        success = set_media_description(file_id, description)
        if not success:
            raise HTTPException(status_code=500, detail="描述更新失败")
        
        # 在向量数据库中查找与file_id匹配的记录
        try:
            from app.services.task_manager import get_task_manager
            from app.database.qdrant_manager import get_qdrant_manager
            
            # 获取向量数据库管理器
            qdrant_manager = get_qdrant_manager()
            
            # 通过滚动查询所有记录，查找file_name匹配的记录
            scroll_result = qdrant_manager.client.scroll(
                collection_name=qdrant_manager.collection_name,
                limit=100,  # 增加限制以确保找到记录
                with_payload=True,
                with_vectors=False  # 不需要向量数据，只需要payload
            )
            
            records = scroll_result[0]
            matching_record = None
            
            # 查找匹配的记录
            for record in records:
                payload = record.payload
                stored_file_name = payload.get('file_name', '')
                stored_file_id = payload.get('file_id', '')
                
                # 尝试多种匹配方式
                if (stored_file_name == file_id or 
                    stored_file_id == file_id or 
                    stored_file_name.endswith(file_id) or 
                    file_id.endswith(stored_file_name)):
                    matching_record = record
                    logger.info(f"找到匹配的向量记录: {record.id} (payload file_name: {stored_file_name})")
                    break
            
            if not matching_record:
                logger.warning(f"未在向量数据库中找到匹配的记录: {file_id}")
                return {"success": True, "message": "描述更新成功，但未找到对应的向量记录"}
            
            # 使用找到的记录ID和全局媒体ID
            vector_record_id = matching_record.id
            global_media_id = matching_record.payload.get('global_media_id', str(vector_record_id))
            
            logger.info(f"使用向量记录ID: {vector_record_id}, 全局媒体ID: {global_media_id}")
            
            # 添加后台任务更新embedding (使用找到的全局媒体ID)
            task_manager = get_task_manager()
            task_id = task_manager.add_description_update_task(
                media_id=global_media_id,  # 使用向量数据库中存储的全局媒体ID
                new_description=description,
                file_path=file_id
            )
            
            logger.info(f"已添加描述更新任务: {task_id} (文件: {file_id}, 向量ID: {vector_record_id})")
            
            return {
                "success": True, 
                "message": "描述更新成功，embedding将在后台更新",
                "embedding_task_id": task_id,
                "global_media_id": global_media_id,
                "vector_record_id": vector_record_id
            }
            
        except Exception as e:
            logger.warning(f"添加描述更新任务失败: {str(e)}")
            # 即使任务添加失败，描述本身已经更新成功
            return {"success": True, "message": "描述更新成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
