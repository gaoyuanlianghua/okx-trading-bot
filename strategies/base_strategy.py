from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, trading_bot):
        """初始化策略
        
        Args:
            trading_bot: 交易机器人实例
        """
        self.trading_bot = trading_bot
        self.running = False
        self.name = self.__class__.__name__
        
    @abstractmethod
    def start(self):
        """启动策略"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止策略"""
        pass
    
    @abstractmethod
    def update(self, market_data: Dict[str, Any]):
        """更新策略
        
        Args:
            market_data: 市场数据
        """
        pass
    
    def log(self, message: str):
        """记录日志
        
        Args:
            message: 日志消息
        """
        logger.info(f"[{self.name}] {message}")
    
    def place_order(self, **kwargs):
        """下单
        
        Args:
            **kwargs: 订单参数
            
        Returns:
            下单结果
        """
        if self.trading_bot:
            return self.trading_bot.place_order(**kwargs)
        return None
    
    def cancel_order(self, **kwargs):
        """撤单
        
        Args:
            **kwargs: 撤单参数
            
        Returns:
            撤单结果
        """
        if self.trading_bot:
            return self.trading_bot.cancel_order(**kwargs)
        return None
    
    def get_market_data(self, inst_id: str):
        """获取市场数据
        
        Args:
            inst_id: 交易对
            
        Returns:
            市场数据
        """
        if self.trading_bot:
            return self.trading_bot.get_market_data(inst_id)
        return None
    
    def get_account_balance(self):
        """获取账户余额
        
        Returns:
            账户余额
        """
        if self.trading_bot:
            return self.trading_bot.get_account_balance()
        return None
    
    def get_position(self, inst_id: str = None):
        """获取持仓信息
        
        Args:
            inst_id: 交易对
            
        Returns:
            持仓信息
        """
        if self.trading_bot:
            return self.trading_bot.get_position(inst_id)
        return None
