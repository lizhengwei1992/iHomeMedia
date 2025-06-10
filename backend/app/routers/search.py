"""
搜索API路由
提供多模态搜索、相似内容推荐等功能
"""

from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
import tempfile
import os
import logging

from app.core.security import get_current_user
from app.models.search_models import (
    SearchRequest, 
    SearchResponse, 
    SimilarMediaRequest,
    BatchEmbeddingRequest,
    EmbeddingStats
)
from app.services.vector_storage_service import get_vector_storage_service
from app.services.embedding_service import get_embedding_service
from app.services.rate_limiter import get_rate_limiter
from app.utils.media_processor import create_thumbnail, is_valid_image
from app.core.config import settings, MEDIA_ROOT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["搜索"])

@router.post("/text", response_model=SearchResponse)
async def search_by_text(
    request: SearchRequest,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    基于文本查询的搜索（优先级最高，直接处理）
    策略：同时搜索文本模态和图像模态，合并去重返回结果
    """
    try:
        # 使用任务管理器处理搜索（最高优先级）
        from app.services.task_manager import get_task_manager
        task_manager = get_task_manager()
        
        # 执行搜索（使用配置的固定阈值）
        search_results = await task_manager.handle_search_query(
            query=request.query,
            limit=request.limit
        )
        
        if not search_results['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"搜索失败: {search_results.get('error', '未知错误')}"
            )
        
        return SearchResponse(
            success=True,
            query=request.query,
            total_results=len(search_results['results']),
            results=search_results['results'],
            search_time=search_results.get('search_time', 0),
            embedding_time=search_results.get('embedding_time', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本搜索异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索异常: {str(e)}"
        )

@router.post("/similar", response_model=SearchResponse)
async def find_similar_media(
    request: SimilarMediaRequest,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    基于媒体ID查找相似内容
    """
    try:
        vector_service = get_vector_storage_service()
        
        # 查找相似内容 - 不使用用户传入的阈值，始终使用配置的阈值
        search_results = await vector_service.find_similar_media(
            media_id=request.media_id,
            limit=request.limit,
            similarity_type=request.similarity_type
            # threshold参数不传递，让服务使用配置的阈值
        )
        
        if not search_results['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"相似内容查找失败: {search_results.get('error', '未知错误')}"
            )
        
        return SearchResponse(
            success=True,
            query=f"media_id:{request.media_id}",
            total_results=len(search_results['results']),
            results=search_results['results'],
            search_time=search_results.get('search_time', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"相似内容查找异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找异常: {str(e)}"
        )

@router.post("/batch-embed")
async def batch_generate_embeddings(
    request: BatchEmbeddingRequest,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    批量生成embeddings（用于数据迁移）
    """
    try:
        vector_service = get_vector_storage_service()
        
        # 执行批量embedding生成
        results = await vector_service.batch_generate_embeddings(
            media_files=request.media_files,
            max_concurrent=request.max_concurrent,
            skip_existing=request.skip_existing
        )
        
        return {
            "success": True,
            "total_files": len(request.media_files),
            "processed": len([r for r in results if r['success']]),
            "failed": len([r for r in results if not r['success']]),
            "results": results,
            "processing_time": sum(r.get('processing_time', 0) for r in results)
        }
        
    except Exception as e:
        logger.error(f"批量embedding生成异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量处理异常: {str(e)}"
        )

@router.get("/stats", response_model=EmbeddingStats)
async def get_embedding_stats(
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取embedding数据库统计信息
    """
    try:
        vector_service = get_vector_storage_service()
        
        # 获取统计信息
        stats = await vector_service.get_collection_stats()
        
        return EmbeddingStats(**stats)
        
    except Exception as e:
        logger.error(f"获取统计信息异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计异常: {str(e)}"
        )

@router.get("/rate-limit-status")
async def get_rate_limit_status(
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取API调用速率限制状态
    """
    try:
        # 获取全局速率限制器状态
        from app.services.task_queue import get_rate_limiter as get_global_rate_limiter
        global_rate_limiter = get_global_rate_limiter()
        global_status = global_rate_limiter.get_status()
        
        # 获取旧版速率限制器状态（向后兼容）
        rate_limiter = get_rate_limiter()
        local_status = rate_limiter.get_status()
        
        return {
            "success": True,
            "global_rate_limiter": global_status,
            "local_rate_limiter": local_status,
            "embedding_service": "DashScope MultiModal Embedding v1"
        }
        
    except Exception as e:
        logger.error(f"获取速率限制状态异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态异常: {str(e)}"
        )

@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取任务状态
    """
    try:
        from app.services.task_manager import get_task_manager
        task_manager = get_task_manager()
        
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        return {
            "success": True,
            "task": task_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态异常: {str(e)}"
        )

@router.get("/queue-stats")
async def get_queue_stats(
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    获取任务队列统计信息
    """
    try:
        from app.services.task_manager import get_task_manager
        task_manager = get_task_manager()
        
        queue_stats = task_manager.get_queue_stats()
        
        return {
            "success": True,
            "stats": queue_stats
        }
        
    except Exception as e:
        logger.error(f"获取队列统计异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队列统计异常: {str(e)}"
        )

@router.post("/migrate-descriptions")
async def migrate_descriptions(
    current_user: str = Depends(get_current_user),
    force: bool = Query(False, description="强制重新生成所有embeddings")
) -> Any:
    """
    迁移现有描述数据到向量数据库
    将JSON文件中的描述与缩略图组合生成embeddings
    """
    try:
        vector_service = get_vector_storage_service()
        
        # 执行数据迁移
        migration_results = await vector_service.migrate_existing_descriptions(
            force_regenerate=force
        )
        
        return {
            "success": True,
            "migration_completed": True,
            "total_processed": migration_results.get('total_processed', 0),
            "successful": migration_results.get('successful', 0),
            "failed": migration_results.get('failed', 0),
            "skipped": migration_results.get('skipped', 0),
            "processing_time": migration_results.get('processing_time', 0),
            "details": migration_results.get('details', [])
        }
        
    except Exception as e:
        logger.error(f"数据迁移异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"迁移异常: {str(e)}"
        )

@router.post("/by-image", response_model=SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    limit: int = Query(100, ge=1, le=500, description="返回结果数量限制"),
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    基于图像的搜索功能（以图搜图）
    
    Args:
        image: 上传的图像文件
        limit: 返回结果数量限制
        current_user: 当前用户
        
    Returns:
        SearchResponse: 搜索结果
    """
    temp_files = []  # 用于跟踪临时文件，确保清理
    
    try:
        # 1. 验证文件类型
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持图像文件"
            )
        
        # 2. 读取并验证图像内容
        image_content = await image.read()
        if not is_valid_image(image_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的图像文件"
            )
        
        # 3. 创建临时文件保存原始图像
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(image.filename or '.jpg')[1],
            delete=False
        ) as temp_file:
            temp_file.write(image_content)
            temp_original_path = temp_file.name
            temp_files.append(temp_original_path)
        
        logger.info(f"以图搜图: 临时保存图像 {image.filename} 到 {temp_original_path}")
        
        # 4. 生成缩略图
        thumbnail_path = create_thumbnail(temp_original_path)
        if thumbnail_path:
            temp_files.append(thumbnail_path)
            processing_image_path = thumbnail_path
            logger.info(f"使用缩略图进行搜索: {thumbnail_path}")
        else:
            processing_image_path = temp_original_path
            logger.info(f"缩略图生成失败，使用原图进行搜索: {temp_original_path}")
        
        # 5. 生成图像embedding
        embedding_service = get_embedding_service()
        
        logger.info(f"开始生成图像embedding...")
        embedding_result = await embedding_service.embed_image_from_file(processing_image_path)
        
        if not embedding_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"图像embedding生成失败: {embedding_result.get('error', '未知错误')}"
            )
        
        image_embedding = embedding_result['embedding']
        logger.info(f"成功生成图像embedding: {len(image_embedding)}维")
        
        # 6. 在向量数据库中搜索相似图像
        from app.database.qdrant_manager import get_qdrant_manager
        qdrant_manager = get_qdrant_manager()
        
        logger.info(f"开始在向量数据库中搜索相似图像...")
        
        search_results = await qdrant_manager.search_by_image(
            query_vector=image_embedding,
            limit=limit,
            score_threshold=None  # 使用配置的默认阈值
        )
        
        logger.info(f"图像搜索完成，找到 {len(search_results)} 个结果")
        
        # 7. 处理搜索结果，转换为与文本搜索一致的格式
        formatted_results = []
        for result in search_results:
            # 保持与文本搜索一致的数据结构：包含metadata字段
            formatted_result = {
                'media_id': str(result['media_id']),
                'score': result['score'],
                'metadata': result.get('metadata', {}),
                'match_type': 'image'
            }
            formatted_results.append(formatted_result)
        
        return SearchResponse(
            success=True,
            query=f"image_search:{image.filename}",
            total_results=len(formatted_results),
            results=formatted_results,
            search_time=embedding_result.get('processing_time', 0),
            embedding_time=embedding_result.get('processing_time', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"以图搜图异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索异常: {str(e)}"
        )
    finally:
        # 8. 清理临时文件
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"已删除临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"删除临时文件失败 {temp_file}: {str(e)}")

@router.post("/similar-by-file", response_model=SearchResponse)
async def search_similar_by_file_path(
    file_path: str = Form(..., description="媒体文件路径"),
    limit: int = Query(100, ge=1, le=500, description="返回结果数量限制"),
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    基于现有媒体文件路径的相似图片搜索功能
    用于查看器中的"找相似"功能
    
    Args:
        file_path: 媒体文件路径
        limit: 返回结果数量限制
        current_user: 当前用户
        
    Returns:
        SearchResponse: 搜索结果
    """
    try:
        # 1. 验证文件路径和类型
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件路径不能为空"
            )
        
        # 构建完整的文件路径
        import os
        full_file_path = os.path.join(MEDIA_ROOT, file_path)
        
        if not os.path.exists(full_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件不存在: {file_path}"
            )
        
        # 验证是否为图片文件
        if not file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持图片文件的相似搜索"
            )
        
        logger.info(f"相似图片搜索: 使用文件 {file_path}")
        
        # 2. 尝试使用缩略图，如果没有则使用原图
        from app.utils.media_processor import create_thumbnail
        
        # 检查缩略图是否存在
        thumbnail_dir = os.path.join(MEDIA_ROOT, "thumbnails")
        thumbnail_rel_path = file_path
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_rel_path)
        
        if os.path.exists(thumbnail_path):
            processing_image_path = thumbnail_path
            logger.info(f"使用现有缩略图: {thumbnail_path}")
        else:
            # 如果缩略图不存在，为原图生成缩略图
            thumbnail_path = create_thumbnail(full_file_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                processing_image_path = thumbnail_path
                logger.info(f"生成新缩略图: {thumbnail_path}")
            else:
                processing_image_path = full_file_path
                logger.info(f"使用原图: {full_file_path}")
        
        # 3. 生成图像embedding
        embedding_service = get_embedding_service()
        
        logger.info(f"开始生成图像embedding...")
        embedding_result = await embedding_service.embed_image_from_file(processing_image_path)
        
        if not embedding_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"图像embedding生成失败: {embedding_result.get('error', '未知错误')}"
            )
        
        image_embedding = embedding_result['embedding']
        logger.info(f"成功生成图像embedding: {len(image_embedding)}维")
        
        # 4. 在向量数据库中搜索相似图像（排除自己）
        from app.database.qdrant_manager import get_qdrant_manager
        qdrant_manager = get_qdrant_manager()
        
        logger.info(f"开始在向量数据库中搜索相似图像...")
        
        search_results = await qdrant_manager.search_by_image(
            query_vector=image_embedding,
            limit=limit + 10,  # 多获取一些，用于排除当前文件
            score_threshold=None  # 使用配置的默认阈值
        )
        
        logger.info(f"图像搜索完成，找到 {len(search_results)} 个结果")
        
        # 5. 过滤掉当前文件本身（通过路径匹配）
        filtered_results = []
        for result in search_results:
            metadata = result.get('metadata', {})
            result_path = metadata.get('relative_path', '') or metadata.get('file_path', '')
            
            # 跳过当前文件
            if result_path == file_path:
                continue
                
            # 保持与其他搜索一致的数据结构：包含metadata字段
            formatted_result = {
                'media_id': str(result['media_id']),
                'score': result['score'],
                'metadata': result.get('metadata', {}),
                'match_type': 'similar_image'
            }
            filtered_results.append(formatted_result)
            
            # 达到指定数量后停止
            if len(filtered_results) >= limit:
                break
        
        return SearchResponse(
            success=True,
            query=f"similar_search:{os.path.basename(file_path)}",
            total_results=len(filtered_results),
            results=filtered_results,
            search_time=embedding_result.get('processing_time', 0),
            embedding_time=embedding_result.get('processing_time', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"相似图片搜索异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索异常: {str(e)}"
        ) 