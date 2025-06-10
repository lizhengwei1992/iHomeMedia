"""
搜索功能相关的数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from app.core.config import settings

class SearchType(str, Enum):
    """搜索类型枚举"""
    TEXT = "text"           # 纯文本搜索
    IMAGE = "image"         # 图像内容搜索
    MULTIMODAL = "multimodal"  # 多模态混合搜索

class MediaType(str, Enum):
    """媒体类型枚举"""
    PHOTO = "photo"
    VIDEO = "video"
    ALL = "all"

class SearchFilters(BaseModel):
    """搜索过滤条件"""
    file_type: Optional[MediaType] = None
    date_range: Optional[Dict[str, str]] = None  # {"start": "2024-01-01", "end": "2024-12-31"}
    tags: Optional[List[str]] = None
    file_size_range: Optional[Dict[str, int]] = None  # {"min": 0, "max": 1000000}

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询文本")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量限制")
    threshold: float = Field(default=settings.SEARCH_THRESHOLD, ge=0.0, le=1.0, description="相似度阈值")

class SimilarSearchRequest(BaseModel):
    """相似内容搜索请求"""
    media_id: str = Field(..., description="参考媒体文件ID")
    search_type: SearchType = Field(default=SearchType.MULTIMODAL, description="搜索类型")
    filters: Optional[SearchFilters] = Field(default=None, description="搜索过滤条件")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量限制")
    score_threshold: float = Field(default=settings.SEARCH_THRESHOLD, ge=0.0, le=1.0, description="相似度阈值")

class MediaSearchResult(BaseModel):
    """单个媒体搜索结果"""
    media_id: str = Field(..., description="媒体文件ID")
    file_path: str = Field(..., description="文件路径")
    file_name: str = Field(..., description="文件名")
    file_type: MediaType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: str = Field(..., description="上传时间")
    description: Optional[str] = Field(default=None, description="文件描述")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    score: float = Field(..., description="相似度评分")
    thumbnail_path: Optional[str] = Field(default=None, description="缩略图路径")

class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool = Field(..., description="搜索是否成功")
    query: str = Field(..., description="原始查询文本")
    total_results: int = Field(..., description="总结果数量")
    results: List[Dict[str, Any]] = Field(..., description="搜索结果列表")
    search_time: float = Field(..., description="搜索耗时（秒）")
    embedding_time: Optional[float] = Field(default=None, description="Embedding生成耗时（秒）")
    search_type: Optional[str] = Field(default=None, description="搜索类型")
    filters_applied: Optional[SearchFilters] = Field(default=None, description="应用的过滤条件")

class EmbeddingData(BaseModel):
    """Embedding数据模型"""
    media_id: str = Field(..., description="媒体文件ID")
    text_embedding: List[float] = Field(..., description="文本embedding向量")
    image_embedding: List[float] = Field(..., description="图像embedding向量")
    metadata: Dict[str, Any] = Field(..., description="元数据")

class EmbeddingRequest(BaseModel):
    """Embedding生成请求"""
    media_id: str = Field(..., description="媒体文件ID")
    file_path: str = Field(..., description="文件路径")
    description: Optional[str] = Field(default=None, description="文件描述")
    force_regenerate: bool = Field(default=False, description="是否强制重新生成")

class EmbeddingResponse(BaseModel):
    """Embedding生成响应"""
    success: bool = Field(..., description="生成是否成功")
    media_id: str = Field(..., description="媒体文件ID")
    text_embedding_generated: bool = Field(..., description="是否生成了文本embedding")
    image_embedding_generated: bool = Field(..., description="是否生成了图像embedding")
    processing_time: float = Field(..., description="处理耗时（秒）")
    error_message: Optional[str] = Field(default=None, description="错误信息")

class BatchEmbeddingRequest(BaseModel):
    """批量Embedding生成请求"""
    media_files: List[EmbeddingRequest] = Field(..., description="媒体文件列表")
    batch_size: int = Field(default=10, ge=1, le=50, description="批处理大小")
    parallel_workers: int = Field(default=3, ge=1, le=10, description="并行工作线程数")

class BatchEmbeddingResponse(BaseModel):
    """批量Embedding生成响应"""
    success: bool = Field(..., description="批处理是否成功")
    total_count: int = Field(..., description="总文件数量")
    success_count: int = Field(..., description="成功处理数量")
    failed_count: int = Field(..., description="失败处理数量")
    results: List[EmbeddingResponse] = Field(..., description="处理结果列表")
    total_time: float = Field(..., description="总处理时间（秒）")

class DatabaseStats(BaseModel):
    """数据库统计信息"""
    collection_name: str = Field(..., description="集合名称")
    total_embeddings: int = Field(..., description="总embedding数量")
    text_embeddings: int = Field(..., description="文本embedding数量")
    image_embeddings: int = Field(..., description="图像embedding数量")
    last_updated: Optional[str] = Field(default=None, description="最后更新时间")
    
class AutoTagRequest(BaseModel):
    """自动标签生成请求"""
    media_id: str = Field(..., description="媒体文件ID")
    file_path: str = Field(..., description="文件路径")
    existing_description: Optional[str] = Field(default=None, description="现有描述")

class AutoTagResponse(BaseModel):
    """自动标签生成响应"""
    success: bool = Field(..., description="生成是否成功")
    media_id: str = Field(..., description="媒体文件ID")
    generated_tags: List[str] = Field(..., description="生成的标签列表")
    generated_description: Optional[str] = Field(default=None, description="生成的描述")
    confidence: float = Field(..., description="置信度")
    processing_time: float = Field(..., description="处理耗时（秒）")
    error_message: Optional[str] = Field(default=None, description="错误信息")

# 兼容性模型定义
class EmbeddingStats(BaseModel):
    """Embedding统计信息（数据库统计的子集）"""
    collection_name: str = Field(..., description="集合名称")
    total_embeddings: int = Field(..., description="总embedding数量")
    vectors_count: int = Field(..., description="向量数量")
    status: str = Field(..., description="状态")
    vector_dimension: int = Field(..., description="向量维度")
    model_name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="服务提供商")

class SimilarMediaRequest(BaseModel):
    """相似媒体查找请求"""
    media_id: str = Field(..., description="参考媒体文件ID")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量限制")
    threshold: float = Field(default=settings.SEARCH_THRESHOLD, ge=0.0, le=1.0, description="相似度阈值")
    similarity_type: str = Field(default="multimodal", description="相似性类型")

class BatchEmbeddingRequest(BaseModel):
    """批量embedding生成请求"""
    media_files: List[Dict[str, Any]] = Field(..., description="媒体文件信息列表")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="最大并发数")
    skip_existing: bool = Field(default=True, description="是否跳过已存在的embeddings") 