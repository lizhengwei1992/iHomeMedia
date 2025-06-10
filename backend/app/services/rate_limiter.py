"""
速率限制服务
控制阿里云API调用频率，避免超出限制
"""

import asyncio
import time
import logging
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_calls: int = 120, time_window: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_calls: 时间窗口内最大调用次数
            time_window: 时间窗口（秒）
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()  # 存储调用时间戳
        self._lock = asyncio.Lock()
        
        logger.info(f"速率限制器初始化: {max_calls}次/{time_window}秒")
    
    async def acquire(self) -> bool:
        """
        获取调用许可
        
        Returns:
            bool: 是否获得许可
        """
        async with self._lock:
            current_time = time.time()
            
            # 清理过期的调用记录
            while self.calls and current_time - self.calls[0] > self.time_window:
                self.calls.popleft()
            
            # 检查是否超出限制
            if len(self.calls) >= self.max_calls:
                # 计算需要等待的时间
                oldest_call = self.calls[0]
                wait_time = self.time_window - (current_time - oldest_call)
                
                if wait_time > 0:
                    logger.warning(f"速率限制触发，需等待 {wait_time:.2f} 秒")
                    return False
            
            # 记录这次调用
            self.calls.append(current_time)
            return True
    
    async def wait_for_permit(self) -> None:
        """
        等待直到获得调用许可
        """
        while not await self.acquire():
            # 计算等待时间
            current_time = time.time()
            if self.calls:
                oldest_call = self.calls[0]
                wait_time = max(1.0, self.time_window - (current_time - oldest_call))
            else:
                wait_time = 1.0
            
            logger.info(f"等待速率限制解除，等待时间: {wait_time:.2f}秒")
            await asyncio.sleep(min(wait_time, 5.0))  # 最多等待5秒后重试
    
    def get_status(self) -> dict:
        """获取当前状态"""
        current_time = time.time()
        
        # 清理过期记录
        while self.calls and current_time - self.calls[0] > self.time_window:
            self.calls.popleft()
        
        return {
            'current_calls': len(self.calls),
            'max_calls': self.max_calls,
            'time_window': self.time_window,
            'available_calls': self.max_calls - len(self.calls),
            'reset_time': self.calls[0] + self.time_window if self.calls else current_time
        }

class AdaptiveRateLimiter(RateLimiter):
    """自适应速率限制器，根据错误率动态调整"""
    
    def __init__(self, max_calls: int = 120, time_window: int = 60, min_calls: int = 60):
        super().__init__(max_calls, time_window)
        self.min_calls = min_calls
        self.original_max_calls = max_calls
        self.error_count = 0
        self.success_count = 0
        self.last_adjustment = time.time()
        
    async def record_success(self):
        """记录成功调用"""
        self.success_count += 1
        await self._adjust_rate()
    
    async def record_error(self, error_type: str = "rate_limit"):
        """记录错误调用"""
        if error_type == "rate_limit":
            self.error_count += 1
            # 立即降低速率
            new_max = max(self.min_calls, int(self.max_calls * 0.8))
            if new_max != self.max_calls:
                logger.warning(f"检测到速率限制错误，降低调用频率: {self.max_calls} -> {new_max}")
                self.max_calls = new_max
        
        await self._adjust_rate()
    
    async def _adjust_rate(self):
        """动态调整速率"""
        current_time = time.time()
        
        # 每分钟调整一次
        if current_time - self.last_adjustment < 60:
            return
        
        total_calls = self.success_count + self.error_count
        if total_calls < 10:  # 样本太少，不调整
            return
        
        error_rate = self.error_count / total_calls
        
        if error_rate < 0.05:  # 错误率小于5%，可以增加速率
            new_max = min(self.original_max_calls, int(self.max_calls * 1.1))
            if new_max != self.max_calls:
                logger.info(f"错误率低，增加调用频率: {self.max_calls} -> {new_max}")
                self.max_calls = new_max
        elif error_rate > 0.15:  # 错误率大于15%，需要降低速率
            new_max = max(self.min_calls, int(self.max_calls * 0.9))
            if new_max != self.max_calls:
                logger.warning(f"错误率高，降低调用频率: {self.max_calls} -> {new_max}")
                self.max_calls = new_max
        
        # 重置计数器
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = current_time

# 全局速率限制器实例
_rate_limiter: Optional[AdaptiveRateLimiter] = None

def get_rate_limiter() -> AdaptiveRateLimiter:
    """获取速率限制器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdaptiveRateLimiter(max_calls=120, time_window=60, min_calls=60)
    return _rate_limiter 