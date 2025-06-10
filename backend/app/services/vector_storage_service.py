"""
向量存储服务
管理媒体文件embedding数据的存储、更新和删除
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.database.qdrant_manager import get_qdrant_manager
from app.services.embedding_service import get_embedding_service
from app.models.search_models import EmbeddingData, EmbeddingResponse
from app.core.config import settings
import asyncio
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorStorageService:
    """向量存储服务类"""
    
    def __init__(self):
        """初始化向量存储服务"""
        self.qdrant_manager = get_qdrant_manager()
        self.embedding_service = get_embedding_service()
        logger.info("向量存储服务初始化成功")
    
    async def store_media_embedding(
        self,
        media_id: str,
        file_path: str,
        file_type: str,
        file_size: int,
        upload_time: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        force_regenerate: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResponse:
        """
        为媒体文件生成并存储embedding
        
        Args:
            media_id: 媒体文件唯一ID
            file_path: 文件路径
            file_type: 文件类型
            file_size: 文件大小
            upload_time: 上传时间
            description: 文件描述
            tags: 标签列表
            force_regenerate: 是否强制重新生成
            extra_metadata: 额外元数据
            
        Returns:
            EmbeddingResponse: 处理结果
        """
        start_time = time.time()
        
        try:
            # 检查是否已存在embedding（如果不强制重新生成）
            if not force_regenerate:
                existing_info = await self.get_media_embedding_info(media_id)
                if existing_info:
                    logger.info(f"媒体文件 {media_id} 的embedding已存在，跳过生成")
                    return EmbeddingResponse(
                        success=True,
                        media_id=media_id,
                        text_embedding_generated=False,
                        image_embedding_generated=False,
                        processing_time=time.time() - start_time,
                        error_message="Embedding已存在，跳过生成"
                    )
            
            # 生成embedding
            embedding_result = await self.embedding_service.embed_media_file(file_path, description)
            
            if not embedding_result.get('success'):
                error_msg = ', '.join(embedding_result.get('errors', ['未知错误']))
                return EmbeddingResponse(
                    success=False,
                    media_id=media_id,
                    text_embedding_generated=False,
                    image_embedding_generated=False,
                    processing_time=time.time() - start_time,
                    error_message=f"Embedding生成失败: {error_msg}"
                )
            
            # 准备元数据
            metadata = {
                'global_media_id': media_id,  # 32位全局ID作为主ID
                'file_path': file_path,
                'file_name': file_path.split('/')[-1],
                'file_type': file_type,
                'file_size': file_size,
                'upload_time': upload_time,
                'description': description or '',
                'tags': tags or [],
                'last_updated': datetime.now().isoformat(),
                'embedding_version': '1.0'
            }
            
            # 合并额外的元数据
            if extra_metadata:
                metadata.update(extra_metadata)
            
            # 确保向量维度正确
            text_embedding = embedding_result.get('text_embedding')
            image_embedding = embedding_result.get('image_embedding')
            
            # 如果向量为空或None，用零向量填充
            vector_dim = self.embedding_service.vector_dimension
            text_embedding_generated = False
            image_embedding_generated = False
            
            if not text_embedding or text_embedding is None:
                text_embedding = [0.0] * vector_dim
                logger.info(f"文本embedding为空，使用零向量: {media_id}")
            else:
                text_embedding_generated = True
                
            if not image_embedding or image_embedding is None:
                image_embedding = [0.0] * vector_dim
                logger.info(f"图像embedding为空，使用零向量: {media_id}")
            else:
                image_embedding_generated = True
            
            # 确保即使描述为空也要存储记录到向量数据库
            # 这样后续更新描述时就能找到对应的记录
            success = await self.qdrant_manager.insert_embedding(
                media_id=media_id,
                text_vector=text_embedding,
                image_vector=image_embedding,
                metadata=metadata
            )
            
            if not success:
                return EmbeddingResponse(
                    success=False,
                    media_id=media_id,
                    text_embedding_generated=text_embedding_generated,
                    image_embedding_generated=image_embedding_generated,
                    processing_time=time.time() - start_time,
                    error_message="向量数据库存储失败"
                )
            
            logger.info(f"成功存储媒体文件embedding: {media_id} (文本: {text_embedding_generated}, 图像: {image_embedding_generated})")
            
            return EmbeddingResponse(
                success=True,
                media_id=media_id,
                text_embedding_generated=text_embedding_generated,
                image_embedding_generated=image_embedding_generated,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"存储媒体文件embedding失败 {media_id}: {str(e)}")
            return EmbeddingResponse(
                success=False,
                media_id=media_id,
                text_embedding_generated=False,
                image_embedding_generated=False,
                processing_time=time.time() - start_time,
                error_message=f"处理异常: {str(e)}"
            )
    
    async def update_media_description(
        self,
        media_id: str,
        new_description: str,
        regenerate_embedding: bool = True
    ) -> bool:
        """
        更新媒体文件描述并重新生成文本embedding
        
        Args:
            media_id: 媒体文件ID
            new_description: 新的描述文本
            regenerate_embedding: 是否重新生成embedding
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取现有数据
            existing_info = await self.get_media_embedding_info(media_id)
            if not existing_info:
                logger.error(f"媒体文件 {media_id} 不存在")
                return False
            
            # 更新元数据
            metadata = existing_info['metadata']
            metadata['description'] = new_description
            metadata['last_updated'] = datetime.now().isoformat()
            
            # 获取现有向量
            text_embedding = existing_info.get('text_embedding', [])
            image_embedding = existing_info.get('image_embedding', [])
            
            # 如果需要重新生成文本embedding
            if regenerate_embedding and new_description.strip():
                embedding_result = await self.embedding_service.embed_text(new_description)
                if embedding_result.get('success'):
                    text_embedding = embedding_result['embedding']
                    logger.info(f"重新生成文本embedding: {media_id}")
            
            # 更新向量数据库
            success = await self.qdrant_manager.insert_embedding(
                media_id=media_id,
                text_vector=text_embedding,
                image_vector=image_embedding,
                metadata=metadata
            )
            
            if success:
                logger.info(f"成功更新媒体文件描述: {media_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"更新媒体文件描述失败 {media_id}: {str(e)}")
            return False
    
    async def delete_media_embedding(self, media_id: str) -> bool:
        """
        删除媒体文件的embedding数据
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            success = await self.qdrant_manager.delete_embedding(media_id)
            if success:
                logger.info(f"成功删除媒体文件embedding: {media_id}")
            return success
            
        except Exception as e:
            logger.error(f"删除媒体文件embedding失败 {media_id}: {str(e)}")
            return False
    
    async def get_media_embedding_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        获取媒体文件的embedding信息
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            Dict: embedding信息，如果不存在则返回None
        """
        try:
            # 在Qdrant中搜索特定ID
            results = await self.qdrant_manager.search_by_text(
                query_vector=[0.0] * self.embedding_service.vector_dimension,
                limit=1,
                score_threshold=0.0,
                filters=None
            )
            
            # 这里简化处理，实际应该直接通过ID获取
            # Qdrant的Python客户端支持通过ID获取点
            # 但为了兼容性，我们暂时用这种方式
            
            # TODO: 实现直接通过ID获取点的方法
            # point = self.qdrant_manager.client.retrieve(
            #     collection_name=self.qdrant_manager.collection_name,
            #     ids=[media_id]
            # )
            
            return None  # 暂时返回None，后续完善
            
        except Exception as e:
            logger.error(f"获取媒体文件embedding信息失败 {media_id}: {str(e)}")
            return None
    
    async def batch_store_embeddings(
        self,
        media_files: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[EmbeddingResponse]:
        """
        批量存储媒体文件embedding
        
        Args:
            media_files: 媒体文件信息列表
            max_concurrent: 最大并发数
            
        Returns:
            List[EmbeddingResponse]: 处理结果列表
        """
        if not media_files:
            return []
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_media(media_info: Dict[str, Any]) -> EmbeddingResponse:
            async with semaphore:
                return await self.store_media_embedding(
                    media_id=media_info['media_id'],
                    file_path=media_info['file_path'],
                    file_type=media_info['file_type'],
                    file_size=media_info['file_size'],
                    upload_time=media_info['upload_time'],
                    description=media_info.get('description'),
                    tags=media_info.get('tags'),
                    force_regenerate=media_info.get('force_regenerate', False),
                    extra_metadata=media_info.get('extra_metadata', {})
                )
        
        # 创建任务列表
        tasks = [process_single_media(media_info) for media_info in media_files]
        
        # 执行批量处理
        logger.info(f"开始批量存储 {len(media_files)} 个媒体文件的embedding")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(EmbeddingResponse(
                    success=False,
                    media_id=media_files[i].get('media_id', f'unknown_{i}'),
                    text_embedding_generated=False,
                    image_embedding_generated=False,
                    processing_time=0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        success_count = sum(1 for r in processed_results if r.success)
        logger.info(f"批量embedding存储完成: {success_count}/{len(media_files)} 成功")
        
        return processed_results
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            collection_info = await self.qdrant_manager.get_collection_info()
            
            return {
                'collection_name': collection_info.get('collection_name', ''),
                'total_embeddings': collection_info.get('points_count', 0),
                'vectors_count': collection_info.get('vectors_count', 0),
                'status': collection_info.get('status', 'unknown'),
                'vector_dimension': self.embedding_service.vector_dimension,
                'model_info': self.embedding_service.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {str(e)}")
            return {
                'error': str(e)
            }
    
    async def rebuild_all_embeddings(
        self,
        media_files: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        重建所有媒体文件的embedding
        
        Args:
            media_files: 媒体文件信息列表
            batch_size: 批处理大小
            
        Returns:
            Dict: 重建结果统计
        """
        if not media_files:
            return {
                'success': True,
                'total_count': 0,
                'success_count': 0,
                'failed_count': 0,
                'processing_time': 0
            }
        
        start_time = time.time()
        all_results = []
        
        # 分批处理
        for i in range(0, len(media_files), batch_size):
            batch = media_files[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(media_files) + batch_size - 1)//batch_size}")
            
            # 为批次中的每个文件添加强制重新生成标志
            for media_info in batch:
                media_info['force_regenerate'] = True
            
            batch_results = await self.batch_store_embeddings(batch, max_concurrent=3)
            all_results.extend(batch_results)
        
        # 统计结果
        total_count = len(all_results)
        success_count = sum(1 for r in all_results if r.success)
        failed_count = total_count - success_count
        processing_time = time.time() - start_time
        
        logger.info(f"重建embedding完成: {success_count}/{total_count} 成功, 耗时: {processing_time:.2f}s")
        
        return {
            'success': True,
            'total_count': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'processing_time': processing_time,
            'results': all_results
        }

    async def migrate_existing_descriptions(self, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        迁移现有描述数据到向量数据库
        从JSON文件读取描述，结合缩略图生成embeddings
        
        Args:
            force_regenerate: 是否强制重新生成已存在的embeddings
            
        Returns:
            Dict: 迁移结果统计
        """
        start_time = time.time()
        migration_results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'processing_time': 0,
            'details': []
        }
        
        try:
            # 加载现有描述
            descriptions = load_descriptions()
            logger.info(f"加载了 {len(descriptions)} 个媒体文件描述")
            
            # 获取所有媒体文件
            media_list_result = list_media_files(page=1, page_size=1000)  # 获取所有文件
            all_media_files = []
            
            # 收集所有页面的媒体文件
            current_page = 1
            while True:
                page_result = list_media_files(page=current_page, page_size=100)
                if not page_result.items:
                    break
                all_media_files.extend(page_result.items)
                if len(page_result.items) < 100:  # 最后一页
                    break
                current_page += 1
            
            logger.info(f"发现 {len(all_media_files)} 个媒体文件")
            
            # 准备迁移数据
            migration_files = []
            for media_file in all_media_files:
                media_id = media_file.file_id
                file_path = os.path.join(MEDIA_ROOT, media_file.relative_path)
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    migration_results['details'].append({
                        'media_id': media_id,
                        'status': 'skipped',
                        'reason': '文件不存在'
                    })
                    migration_results['skipped'] += 1
                    continue
                
                # 获取缩略图路径
                thumbnail_path = self._get_thumbnail_path(file_path, media_file.file_type)
                
                # 获取描述
                description = descriptions.get(media_id, "")
                
                migration_files.append({
                    'media_id': media_id,
                    'file_path': thumbnail_path if thumbnail_path and os.path.exists(thumbnail_path) else file_path,
                    'file_type': media_file.file_type,
                    'file_size': media_file.file_size,
                    'upload_time': media_file.create_time.isoformat() if hasattr(media_file, 'create_time') else "",
                    'description': description,
                    'force_regenerate': force_regenerate
                })
            
            migration_results['total_processed'] = len(migration_files)
            
            if migration_files:
                # 执行批量处理
                batch_results = await self.batch_store_embeddings(
                    migration_files,
                    max_concurrent=2  # 降低并发以避免速率限制
                )
                
                # 统计结果
                for i, result in enumerate(batch_results):
                    if result.success:
                        migration_results['successful'] += 1
                        migration_results['details'].append({
                            'media_id': result.media_id,
                            'status': 'success',
                            'processing_time': result.processing_time
                        })
                    else:
                        migration_results['failed'] += 1
                        migration_results['details'].append({
                            'media_id': result.media_id,
                            'status': 'failed',
                            'error': result.error_message
                        })
            
            migration_results['processing_time'] = time.time() - start_time
            
            logger.info(f"数据迁移完成: {migration_results['successful']} 成功, "
                       f"{migration_results['failed']} 失败, "
                       f"{migration_results['skipped']} 跳过, "
                       f"耗时: {migration_results['processing_time']:.2f}s")
            
            return migration_results
            
        except Exception as e:
            logger.error(f"数据迁移异常: {str(e)}")
            migration_results['processing_time'] = time.time() - start_time
            return migration_results
    
    def _get_thumbnail_path(self, file_path: str, file_type: str) -> Optional[str]:
        """获取缩略图路径"""
        try:
            file_path_obj = Path(file_path)
            parent_dir = file_path_obj.parent
            file_stem = file_path_obj.stem
            
            # 查找缩略图文件
            thumbnail_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            for ext in thumbnail_extensions:
                thumbnail_path = parent_dir / f"{file_stem}_thumbnail{ext}"
                if thumbnail_path.exists():
                    return str(thumbnail_path)
            
            # 如果没找到缩略图，对于图片类型返回原文件
            if file_type.upper() == 'PHOTO':
                return file_path
                
            return None
            
        except Exception as e:
            logger.error(f"获取缩略图路径失败: {str(e)}")
            return None

    async def search_by_text(
        self,
        query: str,
        limit: int = 10,
        threshold: float = None
    ) -> Dict[str, Any]:
        """
        基于文本查询进行搜索
        策略：同时搜索文本模态和图像模态，合并去重返回结果
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            threshold: 相似度阈值（如果未提供，使用配置的值）
            
        Returns:
            Dict: 搜索结果
        """
        start_time = time.time()
        
        try:
            # 生成查询embedding
            embedding_start = time.time()
            query_result = await self.embedding_service.embed_text(query)
            embedding_time = time.time() - embedding_start
            
            if not query_result['success']:
                return {
                    'success': False,
                    'error': f"查询embedding生成失败: {query_result.get('error', '未知错误')}"
                }
            
            query_vector = query_result['embedding']
            
            # 使用配置的阈值，不允许修改
            search_threshold = settings.SEARCH_THRESHOLD
            
            # 1. 搜索文本模态
            text_results = await self.qdrant_manager.search_by_text(
                query_vector=query_vector,
                limit=limit * 2,  # 获取更多候选，确保去重后有足够结果
                score_threshold=search_threshold
            )
            
            # 2. 搜索图像模态
            image_results = await self.qdrant_manager.search_by_image(
                query_vector=query_vector,
                limit=limit * 2,  # 获取更多候选，确保去重后有足够结果
                score_threshold=search_threshold
            )
            
            # 3. 合并去重结果
            combined_results = {}
            
            # 添加文本搜索结果
            for result in text_results:
                media_id = result["media_id"]
                combined_results[media_id] = {
                    **result,
                    "search_source": "text_modal",
                    "final_score": result["score"]
                }
            
            # 添加图像搜索结果（去重）
            for result in image_results:
                media_id = result["media_id"]
                if media_id not in combined_results:
                    combined_results[media_id] = {
                        **result,
                        "search_source": "image_modal",
                        "final_score": result["score"]
                    }
                else:
                    # 如果已存在，保留更高的分数，并标记为双重匹配
                    if result["score"] > combined_results[media_id]["final_score"]:
                        combined_results[media_id]["final_score"] = result["score"]
                    combined_results[media_id]["search_source"] = "both_modals"
            
            # 4. 按分数排序并限制数量
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x["final_score"], reverse=True)
            final_results = final_results[:limit]
            
            search_time = time.time() - start_time
            
            logger.info(f"文本查询搜索完成: 文本模态{len(text_results)}个, "
                       f"图像模态{len(image_results)}个, 合并后{len(final_results)}个, "
                       f"阈值{search_threshold}")
            
            return {
                'success': True,
                'results': final_results,
                'search_time': search_time,
                'embedding_time': embedding_time,
                'query': query,
                'threshold_used': search_threshold,
                'text_modal_count': len(text_results),
                'image_modal_count': len(image_results),
                'final_count': len(final_results)
            }
            
        except Exception as e:
            logger.error(f"文本搜索异常: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def find_similar_media(
        self,
        media_id: str,
        limit: int = 10,
        threshold: float = None,
        similarity_type: str = "multimodal"
    ) -> Dict[str, Any]:
        """
        查找相似媒体内容
        
        Args:
            media_id: 媒体ID
            limit: 返回结果数量限制
            threshold: 相似度阈值（如果未提供，使用配置的值）
            similarity_type: 相似性类型
            
        Returns:
            Dict: 搜索结果
        """
        try:
            # 使用配置的阈值，不允许修改
            search_threshold = settings.SEARCH_THRESHOLD
            
            # 获取目标媒体的embedding
            # TODO: 实现通过media_id获取embedding的方法
            # 目前暂时返回空结果
            
            return {
                'success': True,
                'results': [],
                'search_time': 0,
                'media_id': media_id,
                'threshold_used': search_threshold,
                'message': '相似内容查找功能开发中'
            }
            
        except Exception as e:
            logger.error(f"相似内容查找异常: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_generate_embeddings(
        self,
        media_files: List[Dict[str, Any]],
        max_concurrent: int = 3,
        skip_existing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量生成embeddings
        
        Args:
            media_files: 媒体文件信息列表
            max_concurrent: 最大并发数
            skip_existing: 是否跳过已存在的embeddings
            
        Returns:
            List: 处理结果列表
        """
        try:
            # 转换为标准格式
            processed_files = []
            for media_file in media_files:
                processed_files.append({
                    'media_id': media_file.get('media_id'),
                    'file_path': media_file.get('file_path'),
                    'file_type': media_file.get('file_type', 'UNKNOWN'),
                    'file_size': media_file.get('file_size', 0),
                    'upload_time': media_file.get('upload_time', ''),
                    'description': media_file.get('description', ''),
                    'force_regenerate': not skip_existing
                })
            
            # 执行批量处理
            batch_results = await self.batch_store_embeddings(
                processed_files,
                max_concurrent=max_concurrent
            )
            
            # 转换结果格式
            results = []
            for result in batch_results:
                results.append({
                    'success': result.success,
                    'media_id': result.media_id,
                    'processing_time': result.processing_time,
                    'error': result.error_message if not result.success else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"批量生成embeddings异常: {str(e)}")
            return []

    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            stats = await self.get_storage_stats()
            
            return {
                'collection_name': stats.get('collection_name', ''),
                'total_embeddings': stats.get('total_embeddings', 0),
                'vectors_count': stats.get('vectors_count', 0),
                'status': stats.get('status', 'unknown'),
                'vector_dimension': stats.get('vector_dimension', 1024),
                'model_name': 'multimodal-embedding-v1',
                'provider': 'Alibaba Cloud DashScope'
            }
            
        except Exception as e:
            logger.error(f"获取集合统计信息异常: {str(e)}")
            return {
                'error': str(e)
            }


# 全局向量存储服务实例
_vector_storage_service: Optional[VectorStorageService] = None

def get_vector_storage_service() -> VectorStorageService:
    """获取向量存储服务实例"""
    global _vector_storage_service
    if _vector_storage_service is None:
        _vector_storage_service = VectorStorageService()
    return _vector_storage_service 