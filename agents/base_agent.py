from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """代理基类"""
    
    def __init__(self, name: str):
        """初始化代理
        
        Args:
            name: 代理名称
        """
        self.name = name
        self.running = False
        
    @abstractmethod
    def start(self):
        """启动代理"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止代理"""
        pass
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        pass
    
    def log(self, message: str):
        """记录日志
        
        Args:
            message: 日志消息
        """
        logger.info(f"[{self.name}] {message}")
    
    def error(self, message: str):
        """记录错误
        
        Args:
            message: 错误消息
        """
        logger.error(f"[{self.name}] {message}")
    
    def warning(self, message: str):
        """记录警告
        
        Args:
            message: 警告消息
        """
        logger.warning(f"[{self.name}] {message}")
