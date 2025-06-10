"""
Embedding相关的任务处理器
处理文件上传和描述更新的embedding生成任务
"""

import logging
from typing import Dict, Any
from app.services.embedding_service import get_embedding_service
from app.services.vector_storage_service import get_vector_storage_service
from app.utils.file_handler import generate_global_media_id
from app.database.qdrant_manager import get_qdrant_manager

logger = logging.getLogger(__name__)

async def handle_upload_embedding_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理文件上传后的embedding生成任务
    
    Args:
        payload: 包含以下字段的字典
            - file_path: 文件路径
            - thumbnail_path: 缩略图路径  
            - description: 文件描述
            - extra_metadata: 额外元数据
    
    Returns:
        Dict: 任务执行结果
    """
    try:
        file_path = payload['file_path']
        thumbnail_path = payload['thumbnail_path']
        description = payload['description']
        extra_metadata = payload['extra_metadata']
        
        logger.info(f"开始处理上传文件embedding: {file_path}")
        
        # 获取服务实例
        vector_storage = get_vector_storage_service()
        
        # 生成全局媒体ID
        global_media_id = extra_metadata.get('global_media_id')
        if not global_media_id:
            # 如果没有提供全局ID，则生成一个
            global_media_id = generate_global_media_id(
                extra_metadata.get('original_name', ''),
                extra_metadata.get('upload_time', '')
            )
        
        logger.info(f"使用全局媒体ID: {global_media_id}")
        
        # 使用缩略图路径作为处理文件（如果存在且文件存在）
        import os
        processing_file_path = file_path
        if thumbnail_path and os.path.exists(thumbnail_path):
            processing_file_path = thumbnail_path
            logger.info(f"使用缩略图进行embedding生成: {thumbnail_path}")
        else:
            logger.info(f"使用原文件进行embedding生成: {file_path}")
        
        # 直接调用向量存储服务生成并存储embedding
        store_result = await vector_storage.store_media_embedding(
            media_id=global_media_id,
            file_path=processing_file_path,
            file_type=extra_metadata.get('file_type', 'photo'),
            file_size=extra_metadata.get('file_size', 0),
            upload_time=extra_metadata.get('upload_time', ''),
            description=description,
            extra_metadata=extra_metadata,
            force_regenerate=extra_metadata.get('force_regenerate', False)
        )
        
        if not store_result.success:
            raise Exception(f"向量存储失败: {store_result.error_message}")
        
        result = {
            'success': True,
            'media_id': global_media_id,
            'file_path': file_path,
            'thumbnail_path': thumbnail_path,
            'processing_file_path': processing_file_path,
            'text_embedding_generated': store_result.text_embedding_generated,
            'image_embedding_generated': store_result.image_embedding_generated,
            'processing_time': store_result.processing_time
        }
        
        logger.info(f"文件embedding处理完成: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"处理上传文件embedding失败: {str(e)}")
        raise

async def handle_description_update_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理描述更新后的embedding更新任务
    
    Args:
        payload: 包含以下字段的字典
            - media_id: 媒体文件的全局ID
            - new_description: 新的描述文本
            - file_path: 文件路径（可选，用于日志）
    
    Returns:
        Dict: 任务执行结果
    """
    try:
        media_id = payload['media_id']
        new_description = payload['new_description']
        file_path = payload.get('file_path', media_id)
        
        logger.info(f"开始更新描述embedding: {file_path}")
        
        # 获取服务实例
        embedding_service = get_embedding_service()
        qdrant_manager = get_qdrant_manager()
        
        # 生成新的文本embedding
        logger.info(f"生成新的文本embedding: {new_description[:50] if new_description else '(空描述)'}...")
        text_embedding_result = await embedding_service.get_text_embedding(new_description)
        
        if not text_embedding_result.get('success'):
            raise Exception(f"文本embedding生成失败: {text_embedding_result.get('error')}")
        
        text_embedding = text_embedding_result['embedding']
        
        # 记录是否使用了零向量
        if text_embedding_result.get('is_zero_vector'):
            logger.info(f"使用零向量作为文本embedding（描述为空）: {file_path}")
        
        # 更新向量数据库中的文本embedding和描述
        logger.info(f"更新向量数据库: {media_id}")
        
        # 转换全局媒体ID为数字ID（与Qdrant存储格式一致）
        if isinstance(media_id, str) and not media_id.isdigit():
            import hashlib
            # 使用MD5哈希的前7位（28位整数），确保在安全范围内
            point_id = int(hashlib.md5(media_id.encode()).hexdigest()[:7], 16)
            logger.info(f"转换字符串ID {media_id} 为数字ID: {point_id}")
        else:
            point_id = media_id
        
        # 获取现有点的信息
        existing_points = qdrant_manager.client.retrieve(
            collection_name=qdrant_manager.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=True
        )
        
        if not existing_points:
            raise Exception(f"未找到媒体ID: {media_id} (数字ID: {point_id})")
        
        existing_point = existing_points[0]
        existing_payload = existing_point.payload
        existing_vectors = existing_point.vector
        
        # 更新payload中的描述
        updated_payload = existing_payload.copy()
        updated_payload['description'] = new_description
        
        # 构建新的向量（保持图像embedding不变，更新文本embedding）
        if isinstance(existing_vectors, dict):
            # 命名向量格式
            updated_vectors = existing_vectors.copy()
            updated_vectors['text_embedding'] = text_embedding  # 修正字段名
        else:
            # 密集向量格式（假设前1024维是图像，后1024维是文本）
            image_embedding = existing_vectors[:1024]
            updated_vectors = image_embedding + text_embedding
        
        # 更新点
        qdrant_manager.client.upsert(
            collection_name=qdrant_manager.collection_name,
            points=[
                {
                    "id": point_id,  # 使用数字ID
                    "vector": updated_vectors,
                    "payload": updated_payload
                }
            ]
        )
        
        result = {
            'success': True,
            'media_id': media_id,
            'file_path': file_path,
            'new_description': new_description,
            'text_embedding_size': len(text_embedding),
            'updated_at': existing_payload.get('upload_time')
        }
        
        logger.info(f"描述embedding更新完成: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"更新描述embedding失败: {str(e)}")
        raise

async def handle_search_embedding_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理搜索查询的embedding生成任务（高优先级，使用配置的固定阈值）
    
    Args:
        payload: 包含以下字段的字典
            - query: 搜索查询文本
            - limit: 搜索结果限制
    
    Returns:
        Dict: 搜索结果
    """
    try:
        query = payload['query']
        limit = payload.get('limit', 20)
        
        logger.info(f"开始处理搜索查询: {query}")
        
        # 获取服务实例
        vector_storage = get_vector_storage_service()
        
        # 执行搜索（使用配置的固定阈值）
        search_result = await vector_storage.search_by_text(
            query=query,
            limit=limit
        )
        
        if not search_result.get('success'):
            raise Exception(f"搜索失败: {search_result.get('error')}")
        
        result = {
            'success': True,
            'query': query,
            'total_results': len(search_result.get('results', [])),
            'search_time': search_result.get('search_time'),
            'results': search_result.get('results', [])
        }
        
        logger.info(f"搜索查询处理完成: {query} -> {result['total_results']} 个结果")
        return result
        
    except Exception as e:
        logger.error(f"处理搜索查询失败: {str(e)}")
        raise 