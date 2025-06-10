"""
搜索API路由
提供多模态搜索、相似内容推荐等功能
"""

from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

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
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["搜索"])

@router.post("/text", response_model=SearchResponse)
async def search_by_text(
    request: SearchRequest,
    current_user: str = Depends(get_current_user)
) -> Any:
    """
    基于文本查询的搜索
    策略：同时搜索文本模态和图像模态，合并去重返回结果
    """
    try:
        vector_service = get_vector_storage_service()
        
        # 执行搜索 - 不使用用户传入的阈值，始终使用配置的阈值
        search_results = await vector_service.search_by_text(
            query=request.query,
            limit=request.limit
            # threshold参数不传递，让服务使用配置的阈值
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
        rate_limiter = get_rate_limiter()
        status = rate_limiter.get_status()
        
        return {
            "success": True,
            "rate_limit_status": status,
            "embedding_service": "DashScope MultiModal Embedding v1"
        }
        
    except Exception as e:
        logger.error(f"获取速率限制状态异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态异常: {str(e)}"
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