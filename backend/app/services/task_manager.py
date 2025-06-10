"""
任务管理器
负责启动任务队列和注册任务处理器
"""

import asyncio
import logging
from app.services.task_queue import get_task_queue, TaskPriority
from app.services.embedding_task_handlers import (
    handle_upload_embedding_task,
    handle_description_update_task,
    handle_search_embedding_task
)

logger = logging.getLogger(__name__)

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.task_queue = get_task_queue()
        self.is_initialized = False
    
    async def initialize(self):
        """初始化任务管理器"""
        if self.is_initialized:
            return
        
        logger.info("初始化任务管理器...")
        
        # 注册任务处理器
        self.task_queue.register_handler("upload_embedding", handle_upload_embedding_task)
        self.task_queue.register_handler("description_update", handle_description_update_task)
        self.task_queue.register_handler("search_embedding", handle_search_embedding_task)
        
        # 启动worker进程
        await self.task_queue.start_workers()
        
        self.is_initialized = True
        logger.info("任务管理器初始化完成")
    
    async def shutdown(self):
        """关闭任务管理器"""
        if not self.is_initialized:
            return
        
        logger.info("关闭任务管理器...")
        await self.task_queue.stop_workers()
        self.is_initialized = False
        logger.info("任务管理器已关闭")
    
    def add_upload_embedding_task(
        self,
        file_path: str,
        thumbnail_path: str,
        description: str,
        extra_metadata: dict
    ) -> str:
        """添加文件上传embedding生成任务"""
        return self.task_queue.add_task(
            task_type="upload_embedding",
            payload={
                "file_path": file_path,
                "thumbnail_path": thumbnail_path,
                "description": description,
                "extra_metadata": extra_metadata
            },
            priority=TaskPriority.NORMAL,
            max_retries=3
        )
    
    def add_description_update_task(
        self,
        media_id: str,
        new_description: str,
        file_path: str = None
    ) -> str:
        """添加描述更新embedding任务"""
        return self.task_queue.add_task(
            task_type="description_update",
            payload={
                "media_id": media_id,
                "new_description": new_description,
                "file_path": file_path
            },
            priority=TaskPriority.HIGH,
            max_retries=3
        )
    
    async def handle_search_query(
        self,
        query: str,
        limit: int = 20,
        threshold: float = None
    ) -> dict:
        """处理搜索查询（同步处理，最高优先级）"""
        try:
            # 搜索是同步的，不通过任务队列
            from app.services.vector_storage_service import get_vector_storage_service
            vector_storage = get_vector_storage_service()
            
            # 直接调用搜索方法
            search_result = await vector_storage.search_by_text(
                query=query,
                limit=limit,
                threshold=threshold
            )
            
            return search_result
            
        except Exception as e:
            logger.error(f"搜索查询处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        return self.task_queue.get_task_status(task_id)
    
    def get_queue_stats(self) -> dict:
        """获取队列统计信息"""
        return self.task_queue.get_queue_stats()


# 全局任务管理器实例
_task_manager: TaskManager = None

def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager 