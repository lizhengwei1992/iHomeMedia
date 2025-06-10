"""
Qdrant向量数据库管理器
用于管理多模态embedding的存储和检索
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchText
import httpx
from qdrant_client.models import Record, ScoredPoint
from app.core.config import settings

logger = logging.getLogger(__name__)

class QdrantManager:
    """Qdrant向量数据库管理器"""
    
    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        """
        初始化Qdrant客户端
        
        Args:
            host: Qdrant服务器地址
            port: Qdrant服务器端口
            api_key: API密钥（可选）
        """
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = "media_embeddings"
        self.text_vector_name = "text_embedding"
        self.image_vector_name = "image_embedding"
        
        # 向量维度（基于阿里云模型）
        self.vector_dimension = 1024
        
        logger.info(f"Qdrant管理器初始化成功: {host}:{port}")
    
    async def ensure_collection_exists(self) -> bool:
        """
        确保集合存在，如果不存在则创建
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 检查集合是否存在
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"集合 {self.collection_name} 已存在")
                return True
            
            # 创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    self.text_vector_name: VectorParams(
                        size=self.vector_dimension,
                        distance=Distance.COSINE
                    ),
                    self.image_vector_name: VectorParams(
                        size=self.vector_dimension,
                        distance=Distance.COSINE
                    )
                }
            )
            
            logger.info(f"成功创建集合: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            return False
    
    async def insert_embedding(
        self, 
        media_id: str, 
        text_vector: List[float], 
        image_vector: List[float], 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        插入或更新媒体文件的embedding
        
        Args:
            media_id: 媒体文件唯一ID
            text_vector: 文本embedding向量
            image_vector: 图像embedding向量
            metadata: 元数据
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 确保ID是字符串格式的UUID或整数
            point_id = media_id
            if isinstance(media_id, str) and not media_id.isdigit():
                # 如果是字符串但不是数字，尝试转换为hash值
                import hashlib
                point_id = int(hashlib.md5(media_id.encode()).hexdigest()[:15], 16)
            
            # 在元数据中保存原始ID
            metadata['original_media_id'] = media_id
            
            point = PointStruct(
                id=point_id,
                vector={
                    self.text_vector_name: text_vector,
                    self.image_vector_name: image_vector
                },
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"成功插入embedding: {media_id}")
            return True
            
        except Exception as e:
            logger.error(f"插入embedding失败 {media_id}: {str(e)}")
            return False
    
    async def search_by_text(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = None,
        filters: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        在文本embedding集合中搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值（如果未提供，使用配置的值）
            filters: 搜索过滤条件
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 使用配置的文本搜索阈值
            threshold = score_threshold if score_threshold is not None else settings.TEXT_SEARCH_THRESHOLD
            
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=("text_embedding", query_vector),  # 指定搜索text_embedding向量
                limit=limit,
                score_threshold=threshold,
                query_filter=filters,
                with_payload=True
            )
            
            results = []
            for hit in search_result:
                result = {
                    "media_id": hit.id,
                    "score": hit.score,
                    "metadata": hit.payload
                }
                results.append(result)
            
            logger.info(f"文本搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"文本搜索失败: {str(e)}")
            return []
    
    async def search_by_image(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = None,
        filters: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        在图像embedding集合中搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值（如果未提供，使用配置的值）
            filters: 搜索过滤条件
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 使用配置的图像搜索阈值
            threshold = score_threshold if score_threshold is not None else settings.IMAGE_SEARCH_THRESHOLD
            
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=("image_embedding", query_vector),  # 指定搜索image_embedding向量
                limit=limit,
                score_threshold=threshold,
                query_filter=filters,
                with_payload=True
            )
            
            results = []
            for hit in search_result:
                result = {
                    "media_id": hit.id,
                    "score": hit.score,
                    "metadata": hit.payload
                }
                results.append(result)
            
            logger.info(f"图像搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"图像搜索失败: {str(e)}")
            return []
    
    async def search_multimodal(
        self,
        text_vector: Optional[List[float]] = None,
        image_vector: Optional[List[float]] = None,
        limit: int = 10,
        score_threshold: float = None,
        filters: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        多模态搜索：同时搜索文本和图像embedding
        
        Args:
            text_vector: 文本查询向量
            image_vector: 图像查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值（如果未提供，使用配置的值）
            filters: 搜索过滤条件
            
        Returns:
            List[Dict]: 合并后的搜索结果
        """
        try:
            # 使用配置的阈值，不允许修改
            threshold = score_threshold if score_threshold is not None else settings.SEARCH_THRESHOLD
            
            results = []
            
            # 搜索文本模态
            if text_vector:
                text_results = await self.search_by_text(text_vector, limit, threshold, filters)
                results.extend(text_results)
            
            # 搜索图像模态
            if image_vector:
                image_results = await self.search_by_image(image_vector, limit, threshold, filters)
                results.extend(image_results)
            
            # 提高初始搜索的阈值，减少低质量结果
            initial_threshold = max(threshold * 0.7, 0.3)  # 至少0.3的基础阈值
            
            # 合并和重新排序结果
            combined_results = {}
            
            # 添加文本搜索结果
            for result in text_results:
                media_id = result["media_id"]
                combined_results[media_id] = {
                    **result,
                    "combined_score": result["score"],
                    "text_score": result["score"],
                    "image_score": 0.0,
                    "match_type": "text"
                }
            
            # 添加图像搜索结果
            for result in image_results:
                media_id = result["media_id"]
                if media_id in combined_results:
                    # 如果已存在，则合并分数
                    combined_results[media_id]["combined_score"] += result["score"]
                    combined_results[media_id]["image_score"] = result["score"]
                    combined_results[media_id]["match_type"] = "multimodal"
                else:
                    combined_results[media_id] = {
                        **result,
                        "combined_score": result["score"],
                        "text_score": 0.0,
                        "image_score": result["score"],
                        "match_type": "image"
                    }
            
            # 按合并分数排序
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # 应用更严格的最终阈值过滤
            # 对于多模态搜索，要求更高的相似度
            final_threshold = max(threshold, 0.5)  # 最低0.5的阈值
            
            filtered_results = [
                result for result in final_results 
                if result["combined_score"] >= final_threshold
            ][:limit]
            
            # 记录详细的搜索统计
            logger.info(f"多模态搜索完成: "
                       f"文本结果={len(text_results)}, "
                       f"图像结果={len(image_results)}, "
                       f"合并后={len(final_results)}, "
                       f"过滤后={len(filtered_results)}, "
                       f"阈值={final_threshold}")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"多模态搜索失败: {str(e)}")
            return []
    
    async def delete_embedding(self, media_id: str) -> bool:
        """
        删除媒体文件的embedding
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 确保ID格式一致
            point_id = media_id
            if isinstance(media_id, str) and not media_id.isdigit():
                import hashlib
                point_id = int(hashlib.md5(media_id.encode()).hexdigest()[:15], 16)
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[point_id]
                )
            )
            
            logger.info(f"成功删除embedding: {media_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除embedding失败 {media_id}: {str(e)}")
            return False
    
    async def delete_collection(self) -> bool:
        """
        删除整个集合
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"成功删除集合: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败 {self.collection_name}: {str(e)}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            Dict: 集合统计信息
        """
        try:
            # 使用原始HTTP响应避免Pydantic验证错误
            
            # 直接发送HTTP请求获取集合信息
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:6333/collections/{self.collection_name}")
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', {})
                    
                    return {
                        "collection_name": self.collection_name,
                        "points_count": result.get('points_count', 0),
                        "vectors_count": result.get('vectors_count', 0),
                        "status": result.get('status', 'unknown'),
                        "config": {
                            "distance": result.get('config', {}).get('params', {}).get('vectors', {}).get('distance', 'unknown')
                        }
                    }
                else:
                    logger.error(f"HTTP请求失败: {response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            
            # 降级方案：尝试使用基本的统计信息
            try:
                # 尝试简单的点数量统计
                search_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                
                return {
                    "collection_name": self.collection_name,
                    "points_count": "可用（具体数量无法获取）",
                    "vectors_count": "可用",
                    "status": "active",
                    "note": "使用降级统计方案"
                }
                
            except Exception as fallback_error:
                logger.error(f"降级方案也失败: {str(fallback_error)}")
                return {
                    "collection_name": self.collection_name,
                    "error": "无法获取集合统计信息，但集合可能正常工作"
                }
    
    def create_filter(self, conditions: Dict[str, Any]) -> Filter:
        """
        创建搜索过滤条件
        
        Args:
            conditions: 过滤条件字典
            
        Returns:
            Filter: Qdrant过滤对象
        """
        must_conditions = []
        
        # 文件类型过滤
        if "file_type" in conditions:
            must_conditions.append(
                FieldCondition(
                    key="file_type",
                    match=MatchText(text=conditions["file_type"])
                )
            )
        
        # 日期范围过滤
        if "date_range" in conditions:
            date_range = conditions["date_range"]
            if "start" in date_range:
                must_conditions.append(
                    FieldCondition(
                        key="upload_time",
                        range=models.Range(gte=date_range["start"])
                    )
                )
            if "end" in date_range:
                must_conditions.append(
                    FieldCondition(
                        key="upload_time",
                        range=models.Range(lte=date_range["end"])
                    )
                )
        
        # 标签过滤
        if "tags" in conditions:
            for tag in conditions["tags"]:
                must_conditions.append(
                    FieldCondition(
                        key="tags",
                        match=MatchText(text=tag)
                    )
                )
        
        return Filter(must=must_conditions) if must_conditions else None


# 全局Qdrant管理器实例
qdrant_manager: Optional[QdrantManager] = None

def get_qdrant_manager() -> QdrantManager:
    """获取Qdrant管理器实例"""
    global qdrant_manager
    if qdrant_manager is None:
        qdrant_manager = QdrantManager()
    return qdrant_manager

async def init_qdrant():
    """初始化Qdrant数据库"""
    manager = get_qdrant_manager()
    await manager.ensure_collection_exists() 