import asyncio
from typing import Dict, List, Callable, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EventBus:
    """事件总线"""
    
    def __init__(self):
        """初始化事件总线"""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.info(f"订阅事件: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.info(f"取消订阅事件: {event_type}")
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        async with self._lock:
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    try:
                        # 异步执行回调
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            # 同步回调在后台线程执行
                            asyncio.create_task(self._run_sync_callback(callback, data))
                    except Exception as e:
                        logger.error(f"执行事件回调失败: {e}")
    
    async def _run_sync_callback(self, callback: Callable[[Dict[str, Any]], None], data: Dict[str, Any]):
        """在后台线程执行同步回调
        
        Args:
            callback: 回调函数
            data: 事件数据
        """
        try:
            callback(data)
        except Exception as e:
            logger.error(f"执行同步回调失败: {e}")
    
    def get_subscribers(self, event_type: str) -> List[Callable]:
        """获取事件订阅者
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者列表
        """
        return self._subscribers.get(event_type, [])
    
    def get_event_types(self) -> List[str]:
        """获取所有事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._subscribers.keys())
    
    def clear(self):
        """清空所有订阅"""
        self._subscribers.clear()
        logger.info("事件总线已清空")
