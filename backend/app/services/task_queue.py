"""
后台任务队列系统
支持优先级处理和全局速率限制
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from queue import PriorityQueue
import uuid
import threading

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """任务优先级"""
    URGENT = 1      # 搜索查询 - 最高优先级
    HIGH = 2        # 描述更新
    NORMAL = 3      # 文件上传embedding生成
    LOW = 4         # 其他后台任务

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """任务数据结构"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    result: Optional[Any] = None
    
    def __lt__(self, other):
        """优先级比较，数值越小优先级越高"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # 同优先级按创建时间排序
        return self.created_at < other.created_at

class GlobalRateLimiter:
    """全局速率限制器"""
    
    def __init__(self, max_requests_per_minute: int = 120):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests_log = []
        self.lock = threading.Lock()
        
    def can_make_request(self) -> bool:
        """检查是否可以发起请求"""
        with self.lock:
            now = datetime.now()
            # 清理一分钟前的记录
            cutoff = now - timedelta(minutes=1)
            self.requests_log = [req_time for req_time in self.requests_log if req_time > cutoff]
            
            return len(self.requests_log) < self.max_requests_per_minute
    
    def record_request(self):
        """记录一次请求"""
        with self.lock:
            self.requests_log.append(datetime.now())
    
    def get_wait_time(self) -> float:
        """获取需要等待的时间（秒）"""
        with self.lock:
            if len(self.requests_log) < self.max_requests_per_minute:
                return 0.0
            
            # 计算最早的请求什么时候会过期
            oldest_request = min(self.requests_log)
            next_available = oldest_request + timedelta(minutes=1)
            wait_seconds = (next_available - datetime.now()).total_seconds()
            return max(0.0, wait_seconds)
    
    def get_status(self) -> Dict[str, Any]:
        """获取速率限制状态"""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)
            recent_requests = [req for req in self.requests_log if req > cutoff]
            
            return {
                "max_requests_per_minute": self.max_requests_per_minute,
                "current_requests_count": len(recent_requests),
                "remaining_requests": max(0, self.max_requests_per_minute - len(recent_requests)),
                "reset_time": cutoff + timedelta(minutes=1),
                "can_make_request": len(recent_requests) < self.max_requests_per_minute
            }

class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, rate_limiter: GlobalRateLimiter):
        self.queue = PriorityQueue()
        self.rate_limiter = rate_limiter
        self.tasks: Dict[str, Task] = {}  # 任务存储
        self.workers_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.task_handlers: Dict[str, Callable] = {}
        self.max_workers = 3  # 最大并发worker数
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    def add_task(
        self, 
        task_type: str, 
        payload: Dict[str, Any], 
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """添加任务到队列"""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            payload=payload,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        self.queue.put(task)
        
        logger.info(f"添加任务: {task_type} (ID: {task_id}, 优先级: {priority.name})")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
            
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "priority": task.priority.name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error_message": task.error_message,
            "result": task.result
        }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        pending_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
        processing_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.PROCESSING]
        completed_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
        failed_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
        
        # 按优先级统计待处理任务
        priority_stats = {}
        for priority in TaskPriority:
            priority_stats[priority.name] = len([
                task for task in pending_tasks if task.priority == priority
            ])
        
        return {
            "total_tasks": len(self.tasks),
            "pending": len(pending_tasks),
            "processing": len(processing_tasks),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "queue_size": self.queue.qsize(),
            "workers_running": self.workers_running,
            "active_workers": len(self.worker_tasks),
            "priority_distribution": priority_stats,
            "rate_limiter_status": self.rate_limiter.get_status()
        }
    
    async def start_workers(self):
        """启动worker进程"""
        if self.workers_running:
            return
            
        self.workers_running = True
        logger.info(f"启动 {self.max_workers} 个worker进程")
        
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
    
    async def stop_workers(self):
        """停止worker进程"""
        if not self.workers_running:
            return
            
        self.workers_running = False
        logger.info("停止worker进程...")
        
        # 取消所有worker任务
        for worker_task in self.worker_tasks:
            worker_task.cancel()
        
        # 等待worker任务完成
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.worker_tasks.clear()
        logger.info("所有worker进程已停止")
    
    async def _worker(self, worker_name: str):
        """Worker进程"""
        logger.info(f"{worker_name} 启动")
        
        while self.workers_running:
            try:
                # 检查速率限制
                if not self.rate_limiter.can_make_request():
                    wait_time = self.rate_limiter.get_wait_time()
                    if wait_time > 0:
                        logger.info(f"{worker_name} 等待速率限制: {wait_time:.1f}秒")
                        await asyncio.sleep(min(wait_time, 10))  # 最多等待10秒
                        continue
                
                # 获取任务（非阻塞）
                try:
                    task = self.queue.get_nowait()
                except:
                    # 队列为空，等待一会
                    await asyncio.sleep(1)
                    continue
                
                # 检查任务是否还有效
                if task.task_id not in self.tasks:
                    continue
                
                # 更新任务状态
                task.status = TaskStatus.PROCESSING
                logger.info(f"{worker_name} 处理任务: {task.task_type} (ID: {task.task_id})")
                
                try:
                    # 记录请求
                    self.rate_limiter.record_request()
                    
                    # 执行任务
                    handler = self.task_handlers.get(task.task_type)
                    if not handler:
                        raise Exception(f"未找到任务处理器: {task.task_type}")
                    
                    result = await handler(task.payload)
                    
                    # 任务成功
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    logger.info(f"{worker_name} 任务完成: {task.task_id}")
                    
                except Exception as e:
                    # 任务失败
                    error_msg = str(e)
                    task.error_message = error_msg
                    task.retry_count += 1
                    
                    if task.retry_count <= task.max_retries:
                        # 重试
                        task.status = TaskStatus.PENDING
                        self.queue.put(task)
                        logger.warning(f"{worker_name} 任务重试 ({task.retry_count}/{task.max_retries}): {task.task_id} - {error_msg}")
                    else:
                        # 达到最大重试次数，标记为失败
                        task.status = TaskStatus.FAILED
                        logger.error(f"{worker_name} 任务失败: {task.task_id} - {error_msg}")
                
            except asyncio.CancelledError:
                logger.info(f"{worker_name} 被取消")
                break
            except Exception as e:
                logger.error(f"{worker_name} 异常: {str(e)}")
                await asyncio.sleep(1)
        
        logger.info(f"{worker_name} 停止")

# 全局实例
_global_rate_limiter = GlobalRateLimiter(max_requests_per_minute=120)
_global_task_queue = TaskQueue(_global_rate_limiter)

def get_task_queue() -> TaskQueue:
    """获取全局任务队列实例"""
    return _global_task_queue

def get_rate_limiter() -> GlobalRateLimiter:
    """获取全局速率限制器实例"""
    return _global_rate_limiter 