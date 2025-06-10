"""
Embedding服务模块
集成阿里云多模态embedding服务，提供统一的向量化接口
"""

import asyncio
import base64
import os
import time
import logging
from typing import Dict, List, Optional, Any
import dashscope
from http import HTTPStatus

from app.core.config import settings
from app.services.rate_limiter import get_rate_limiter
from app.services.task_queue import get_rate_limiter as get_global_rate_limiter

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Embedding服务类，集成阿里云DashScope API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Embedding服务
        
        Args:
            api_key: 阿里云DashScope API Key
        """
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        if not self.api_key or self.api_key == 'your_dashscope_api_key_here':
            raise ValueError(
                "请提供有效的阿里云 API Key！\n"
                "1. 登录 https://dashscope.console.aliyun.com/ 获取API密钥\n"
                "2. 在 .local.env 文件中设置 DASHSCOPE_API_KEY=您的真实密钥"
            )
        
        # 设置 API Key
        dashscope.api_key = self.api_key
        self.model_name = "multimodal-embedding-v1"
        self.vector_dimension = 1024
        
        logger.info("Embedding服务初始化成功")
    
    async def embed_text(self, text: str) -> Dict[str, Any]:
        """
        文本向量化（异步版本）
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 包含向量和元信息的字典
        """
        if not text or not text.strip():
            # 当文本为空时，返回零向量而不是报错
            logger.info("文本内容为空，返回零向量")
            return {
                'success': True,
                'embedding': [0.0] * self.vector_dimension,
                'type': 'text',
                'dimension': self.vector_dimension,
                'usage': None,
                'request_id': None,
                'is_zero_vector': True  # 标记这是零向量
            }
        
        try:
            # 直接调用异步方法
            result = await self._embed_text_sync(text)
            return result
            
        except Exception as e:
            logger.error(f"异步文本embedding失败: {str(e)}")
            return {
                'success': False,
                'error': f"处理异常: {str(e)}"
            }
    
    async def _embed_text_sync(self, text: str) -> Dict[str, Any]:
        """同步文本向量化（已集成速率限制）"""
        rate_limiter = get_rate_limiter()
        
        try:
            # 等待速率限制许可
            await rate_limiter.wait_for_permit()
            
            input_data = [{'text': text}]
            
            # 在线程池中执行同步API调用
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, 
                lambda: dashscope.MultiModalEmbedding.call(
                    model=self.model_name,
                    input=input_data
                )
            )
            
            if resp.status_code == HTTPStatus.OK:
                # 记录成功调用
                await rate_limiter.record_success()
                
                embedding_data = resp.output['embeddings'][0]
                return {
                    'success': True,
                    'embedding': embedding_data['embedding'],
                    'type': embedding_data['type'],
                    'dimension': len(embedding_data['embedding']),
                    'usage': resp.usage if resp.usage else None,
                    'request_id': resp.request_id
                }
            else:
                # 检查是否为速率限制错误
                if 'rate limit' in str(resp.message).lower() or resp.code == 'Throttling':
                    await rate_limiter.record_error("rate_limit")
                
                logger.error(f"文本embedding请求失败: {resp}")
                return {
                    'success': False,
                    'error': f"API调用失败: {resp.code} - {resp.message}"
                }
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"文本embedding异常: {error_str}")
            
            # 处理不同类型的错误
            if 'rate limit' in error_str.lower() or 'throttl' in error_str.lower():
                await rate_limiter.record_error("rate_limit")
                error_msg = "请求过于频繁，请稍后重试"
            elif 'InvalidApiKey' in error_str or 'Invalid API-key' in error_str:
                error_msg = "API密钥无效，请检查.local.env文件中的DASHSCOPE_API_KEY配置"
            elif 'SSLError' in error_str or 'SSL' in error_str:
                error_msg = "网络连接异常，请检查网络环境或稍后重试"
            elif 'ConnectionError' in error_str or 'Timeout' in error_str:
                error_msg = "网络连接超时，请检查网络环境"
            else:
                error_msg = f"处理异常: {error_str}"
            
            return {
                'success': False,
                'error': error_msg
            }
    
    async def embed_image_from_file(self, image_path: str) -> Dict[str, Any]:
        """
        从本地文件读取图像并向量化（异步版本）
        
        Args:
            image_path: 本地图像文件路径
            
        Returns:
            Dict: 包含向量和元信息的字典
        """
        if not os.path.exists(image_path):
            return {
                'success': False,
                'error': f'图像文件不存在: {image_path}'
            }
        
        try:
            # 直接调用异步方法
            result = await self._embed_image_sync(image_path)
            return result
            
        except Exception as e:
            logger.error(f"异步图像embedding失败: {str(e)}")
            return {
                'success': False,
                'error': f"处理异常: {str(e)}"
            }
    
    async def _embed_image_sync(self, image_path: str) -> Dict[str, Any]:
        """同步图像向量化（已集成速率限制）"""
        rate_limiter = get_rate_limiter()
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                # 等待速率限制许可
                await rate_limiter.wait_for_permit()
                
                # 读取并转换为Base64
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                # 检测图像格式
                image_format = image_path.split('.')[-1].lower()
                if image_format == 'jpg':
                    image_format = 'jpeg'
                
                # 检查图像大小，如果太大则跳过
                file_size = os.path.getsize(image_path)
                if file_size > 8 * 1024 * 1024:  # 8MB限制
                    return {
                        'success': False,
                        'error': f'图像文件过大 ({file_size/1024/1024:.2f}MB)，建议小于8MB'
                    }
                
                image_data = f"data:image/{image_format};base64,{base64_image}"
                input_data = [{'image': image_data}]
                
                # 在线程池中执行同步API调用
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None,
                    lambda: dashscope.MultiModalEmbedding.call(
                        model=self.model_name,
                        input=input_data
                    )
                )
                
                if resp.status_code == HTTPStatus.OK:
                    # 记录成功调用
                    await rate_limiter.record_success()
                    
                    embedding_data = resp.output['embeddings'][0]
                    return {
                        'success': True,
                        'embedding': embedding_data['embedding'],
                        'type': embedding_data['type'],
                        'dimension': len(embedding_data['embedding']),
                        'usage': resp.usage if resp.usage else None,
                        'request_id': resp.request_id,
                        'attempts': attempt + 1
                    }
                else:
                    error_code = getattr(resp, 'code', 'Unknown')
                    error_message = getattr(resp, 'message', 'Unknown error')
                    
                    # 检查是否为可重试的错误
                    is_retryable = (
                        'InternalError' in error_code or
                        'Failed to invoke backend' in error_message or
                        resp.status_code == 500 or
                        'rate limit' in error_message.lower() or 
                        error_code == 'Throttling'
                    )
                    
                    if is_retryable and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # 指数退避
                        logger.warning(f"图像embedding重试 {attempt + 1}/{max_retries}: {error_code} - {error_message}，{delay}秒后重试")
                        await asyncio.sleep(delay)
                        continue
                    
                    # 记录错误
                    if 'rate limit' in error_message.lower() or error_code == 'Throttling':
                        await rate_limiter.record_error("rate_limit")
                    
                    logger.error(f"图像embedding请求失败: {resp}")
                    return {
                        'success': False,
                        'error': f"API调用失败: {error_code} - {error_message}",
                        'attempts': attempt + 1,
                        'retryable': is_retryable
                    }
                    
            except Exception as e:
                error_str = str(e)
                logger.error(f"图像embedding异常 (尝试 {attempt + 1}/{max_retries}): {error_str}")
                
                # 判断是否为可重试的异常
                is_retryable = (
                    'rate limit' in error_str.lower() or 
                    'throttl' in error_str.lower() or
                    'timeout' in error_str.lower() or
                    'connection' in error_str.lower() or
                    'Internal' in error_str
                )
                
                if is_retryable and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"图像embedding异常重试，{delay}秒后重试")
                    await asyncio.sleep(delay)
                    continue
                
                # 处理不同类型的错误
                if 'rate limit' in error_str.lower() or 'throttl' in error_str.lower():
                    await rate_limiter.record_error("rate_limit")
                    error_msg = "请求过于频繁，请稍后重试"
                elif 'InvalidApiKey' in error_str or 'Invalid API-key' in error_str:
                    error_msg = "API密钥无效，请检查.local.env文件中的DASHSCOPE_API_KEY配置"
                elif 'SSLError' in error_str or 'SSL' in error_str:
                    error_msg = "网络连接异常，请检查网络环境或稍后重试"
                elif 'ConnectionError' in error_str or 'Timeout' in error_str:
                    error_msg = "网络连接超时，请检查网络环境"
                else:
                    error_msg = f"处理异常: {error_str}"
                
                return {
                    'success': False,
                    'error': error_msg,
                    'attempts': attempt + 1,
                    'original_error': error_str
                }
        
        # 如果所有重试都失败了
        return {
            'success': False,
            'error': f'图像embedding失败，已尝试 {max_retries} 次',
            'attempts': max_retries
        }
    
    def _get_thumbnail_path(self, file_path: str) -> str:
        """
        获取缩略图路径，如果缩略图不存在则返回原始文件路径
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            str: 缩略图路径或原始文件路径
        """
        try:
            # 构建缩略图路径
            from app.core.config import MEDIA_ROOT
            
            # 获取相对路径
            rel_path = os.path.relpath(file_path, MEDIA_ROOT)
            
            # 构建缩略图路径
            thumbnail_path = os.path.join(MEDIA_ROOT, "thumbnails", rel_path)
            
            # 对于HEIC文件，缩略图是JPEG格式
            if file_path.lower().endswith(('.heic', '.heif')):
                thumbnail_path = thumbnail_path.rsplit('.', 1)[0] + '.jpg'
            
            # 对于视频文件，缩略图是JPEG格式  
            elif file_path.lower().endswith(('.mp4', '.mov', '.hevc', '.avi')):
                thumbnail_path = thumbnail_path.rsplit('.', 1)[0] + '.jpg'
            
            # 如果缩略图存在，返回缩略图路径
            if os.path.exists(thumbnail_path):
                # 检查文件大小，确保缩略图适合API限制
                file_size = os.path.getsize(thumbnail_path)
                if file_size <= 10 * 1024 * 1024:  # 10MB限制
                    logger.info(f"使用缩略图进行embedding: {thumbnail_path} ({file_size/1024/1024:.2f}MB)")
                    return thumbnail_path
                else:
                    logger.warning(f"缩略图过大，跳过: {thumbnail_path} ({file_size/1024/1024:.2f}MB)")
                    return None
            
            # 检查原始文件大小
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size <= 10 * 1024 * 1024:  # 10MB限制
                    logger.info(f"使用原始文件进行embedding: {file_path} ({file_size/1024/1024:.2f}MB)")
                    return file_path
                else:
                    logger.warning(f"原始文件过大，跳过embedding: {file_path} ({file_size/1024/1024:.2f}MB)")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"获取缩略图路径失败: {str(e)}")
            return file_path  # 降级到原始文件

    async def embed_media_file(self, file_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        为媒体文件生成双模态embedding（串行处理以避免速率限制）
        
        Args:
            file_path: 媒体文件路径
            description: 文件描述文本
            
        Returns:
            Dict: 包含文本和图像embedding的字典
        """
        start_time = time.time()
        result = {
            'success': True,
            'file_path': file_path,
            'text_embedding': None,
            'image_embedding': None,
            'text_success': False,
            'image_success': False,
            'processing_time': 0,
            'errors': []
        }
        
        try:
            # 串行处理文本和图像embedding，避免速率限制
            
            # 1. 先处理文本embedding
            logger.info(f"开始处理文本embedding: {file_path}")
            if description and description.strip():
                # 只有在有实际描述时才生成文本embedding
                text_result = await self.embed_text(description)
                
                # 处理文本embedding结果
                if text_result.get('success'):
                    result['text_embedding'] = text_result['embedding']
                    result['text_success'] = True
                    logger.info(f"文本embedding成功: {file_path}")
                else:
                    result['errors'].append(f"文本embedding失败: {text_result.get('error', '未知错误')}")
                    logger.warning(f"文本embedding失败: {file_path} - {text_result.get('error', '未知错误')}")
            else:
                # 没有描述时，不生成文本embedding，记录为跳过
                logger.info(f"没有描述文本，跳过文本embedding生成: {file_path}")
                result['text_embedding'] = None  # 明确设置为None，稍后用零向量填充
            
            # 2. 添加0.5秒间隔，避免速率限制
            logger.info(f"等待0.5秒后处理图像embedding...")
            await asyncio.sleep(0.5)
            
            # 3. 处理图像embedding
            logger.info(f"开始处理图像embedding: {file_path}")
            image_file_path = self._get_thumbnail_path(file_path)
            if image_file_path:
                image_result = await self.embed_image_from_file(image_file_path)
                
                # 处理图像embedding结果
                if image_result.get('success'):
                    result['image_embedding'] = image_result['embedding']
                    result['image_success'] = True
                    logger.info(f"图像embedding成功: {file_path}")
                else:
                    result['errors'].append(f"图像embedding失败: {image_result.get('error', '未知错误')}")
                    logger.warning(f"图像embedding失败: {file_path} - {image_result.get('error', '未知错误')}")
            else:
                result['errors'].append('文件过大，无法生成图像embedding（超过10MB限制）')
                logger.warning(f"文件过大，跳过图像embedding: {file_path}")
            
            # 检查是否至少有一个embedding成功
            if not result['text_success'] and not result['image_success']:
                result['success'] = False
                logger.error(f"文本和图像embedding都失败: {file_path}")
            
            result['processing_time'] = time.time() - start_time
            
            logger.info(f"媒体文件embedding完成: {file_path}, "
                       f"文本: {result['text_success']}, 图像: {result['image_success']}, "
                       f"耗时: {result['processing_time']:.2f}s")
            
            return result
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"处理异常: {str(e)}")
            result['processing_time'] = time.time() - start_time
            logger.error(f"媒体文件embedding异常 {file_path}: {str(e)}")
            return result
    
    async def embed_query_text(self, query: str) -> Dict[str, Any]:
        """
        为搜索查询文本生成embedding（使用全局速率限制器，优先级最高）
        
        Args:
            query: 搜索查询文本
            
        Returns:
            Dict: 包含embedding向量的字典
        """
        if not query or not query.strip():
            # 当查询文本为空时，返回零向量而不是报错
            logger.info("查询文本为空，返回零向量")
            return {
                'success': True,
                'embedding': [0.0] * self.vector_dimension,
                'type': 'text',
                'dimension': self.vector_dimension,
                'usage': None,
                'request_id': None,
                'is_zero_vector': True  # 标记这是零向量
            }
        
        return await self._embed_text_with_global_limiter(query.strip())
    
    async def _embed_text_with_global_limiter(self, text: str) -> Dict[str, Any]:
        """使用全局速率限制器进行文本embedding（搜索专用）"""
        global_rate_limiter = get_global_rate_limiter()
        
        try:
            # 检查全局速率限制
            if not global_rate_limiter.can_make_request():
                wait_time = global_rate_limiter.get_wait_time()
                if wait_time > 0:
                    logger.info(f"等待全局速率限制: {wait_time:.1f}秒")
                    await asyncio.sleep(wait_time)
            
            # 记录请求
            global_rate_limiter.record_request()
            
            input_data = [{'text': text}]
            
            # 在线程池中执行同步API调用
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, 
                lambda: dashscope.MultiModalEmbedding.call(
                    model=self.model_name,
                    input=input_data
                )
            )
            
            if resp.status_code == HTTPStatus.OK:
                embedding_data = resp.output['embeddings'][0]
                return {
                    'success': True,
                    'embedding': embedding_data['embedding'],
                    'type': embedding_data['type'],
                    'dimension': len(embedding_data['embedding']),
                    'usage': resp.usage if resp.usage else None,
                    'request_id': resp.request_id
                }
            else:
                logger.error(f"搜索文本embedding请求失败: {resp}")
                return {
                    'success': False,
                    'error': f"API调用失败: {resp.code} - {resp.message}"
                }
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"搜索文本embedding异常: {error_str}")
            
            # 处理不同类型的错误
            if 'rate limit' in error_str.lower() or 'throttl' in error_str.lower():
                error_msg = "请求过于频繁，请稍后重试"
            elif 'InvalidApiKey' in error_str or 'Invalid API-key' in error_str:
                error_msg = "API密钥无效，请检查.local.env文件中的DASHSCOPE_API_KEY配置"
            elif 'SSLError' in error_str or 'SSL' in error_str:
                error_msg = "网络连接异常，请检查网络环境或稍后重试"
            elif 'ConnectionError' in error_str or 'Timeout' in error_str:
                error_msg = "网络连接超时，请检查网络环境"
            else:
                error_msg = f"处理异常: {error_str}"
            
            return {
                'success': False,
                'error': error_msg
            }
        
    # 为兼容性保留原有方法（用于非搜索的embedding生成）
    async def get_text_embedding(self, text: str) -> Dict[str, Any]:
        """获取文本embedding（为任务队列使用，使用原速率限制器）"""
        return await self.embed_text(text)
    
    async def get_image_embedding(self, image_path: str) -> Dict[str, Any]:
        """获取图像embedding（为任务队列使用，使用原速率限制器）"""
        return await self.embed_image_from_file(image_path)
    
    async def batch_embed_media_files(
        self, 
        file_paths: List[str], 
        descriptions: Optional[List[str]] = None,
        max_concurrent: int = 2,  # 降低默认并发数以避免速率限制
        interval_between_files: float = 1.0  # 文件间处理间隔
    ) -> List[Dict[str, Any]]:
        """
        批量处理媒体文件embedding（考虑速率限制）
        
        Args:
            file_paths: 媒体文件路径列表
            descriptions: 对应的描述列表（可选）
            max_concurrent: 最大并发数（默认2，避免速率限制）
            interval_between_files: 文件间处理间隔（秒）
            
        Returns:
            List[Dict]: 处理结果列表
        """
        if not file_paths:
            return []
        
        logger.info(f"开始批量处理 {len(file_paths)} 个媒体文件，并发数: {max_concurrent}, 间隔: {interval_between_files}秒")
        
        # 准备描述列表
        if descriptions is None:
            descriptions = [None] * len(file_paths)
        elif len(descriptions) != len(file_paths):
            # 补齐描述列表
            descriptions.extend([None] * (len(file_paths) - len(descriptions)))
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_file_with_delay(
            file_index: int, 
            file_path: str, 
            description: Optional[str]
        ) -> Dict[str, Any]:
            """处理单个文件，包含延迟控制"""
            async with semaphore:
                # 为避免同时启动的任务都立即开始，添加基于索引的小延迟
                if file_index > 0:
                    base_delay = (file_index % max_concurrent) * interval_between_files
                    if base_delay > 0:
                        logger.info(f"文件 {file_index} 等待 {base_delay:.1f}秒后开始处理")
                        await asyncio.sleep(base_delay)
                
                logger.info(f"开始处理文件 {file_index + 1}/{len(file_paths)}: {os.path.basename(file_path)}")
                result = await self.embed_media_file(file_path, description)
                
                # 处理完成后再等待一小段时间，确保不会立即开始下一个文件
                if file_index < len(file_paths) - 1:  # 不是最后一个文件
                    await asyncio.sleep(0.2)  # 短暂间隔
                
                return result
        
        # 创建任务列表
        tasks = [
            process_single_file_with_delay(i, file_path, descriptions[i])
            for i, file_path in enumerate(file_paths)
        ]
        
        # 执行所有任务
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"文件 {i} 处理异常: {str(result)}")
                    processed_results.append({
                        'success': False,
                        'file_path': file_paths[i],
                        'error': str(result),
                        'text_success': False,
                        'image_success': False
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"批量处理完成，成功: {sum(1 for r in processed_results if r.get('success', False))} / {len(file_paths)}")
            return processed_results
            
        except Exception as e:
            logger.error(f"批量处理异常: {str(e)}")
            return [{
                'success': False,
                'file_path': file_path,
                'error': f"批量处理异常: {str(e)}",
                'text_success': False,
                'image_success': False
            } for file_path in file_paths]
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension,
            'supported_types': ['text', 'image'],
            'text_max_tokens': 512,
            'image_max_size': '3MB',
            'image_formats': ['JPG', 'JPEG', 'PNG', 'BMP', 'HEIC', 'WEBP']
        }


# 全局embedding服务实例
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """获取embedding服务实例"""
    global _embedding_service
    if _embedding_service is None:
        # 确保在创建服务时API Key已经从配置中读取
        api_key = settings.DASHSCOPE_API_KEY
        _embedding_service = EmbeddingService(api_key=api_key)
    return _embedding_service 