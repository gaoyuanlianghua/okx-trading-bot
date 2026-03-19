from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataAgent(BaseAgent):
    """市场数据代理"""
    
    def __init__(self, trading_bot):
        """初始化市场数据代理
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__("MarketDataAgent")
        self.trading_bot = trading_bot
        self.market_data = {}
        self.last_update_time = {}
        
    def start(self):
        """启动代理"""
        self.running = True
        self.log("市场数据代理启动")
        
    def stop(self):
        """停止代理"""
        self.running = False
        self.log("市场数据代理停止")
        
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.running:
            return None
        
        # 处理市场数据请求
        if data.get("type") == "market_data_request":
            inst_id = data.get("inst_id")
            if inst_id:
                return self.get_market_data(inst_id)
        
        # 处理WebSocket市场数据
        elif data.get("type") == "websocket_market_data":
            self.update_market_data(data.get("data"))
        
        return None
    
    def get_market_data(self, inst_id: str) -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            inst_id: 交易对
            
        Returns:
            市场数据
        """
        # 检查是否有最新数据
        current_time = time.time()
        if inst_id in self.market_data and inst_id in self.last_update_time:
            if current_time - self.last_update_time[inst_id] < 5:  # 5秒内的缓存数据
                return self.market_data[inst_id]
        
        # 从API获取数据
        if self.trading_bot:
            try:
                data = self.trading_bot.get_market_data(inst_id)
                if data and data.get("code") == "0":
                    self.market_data[inst_id] = data
                    self.last_update_time[inst_id] = current_time
                    return data
            except Exception as e:
                self.error(f"获取市场数据失败: {e}")
        
        return {"code": "500", "msg": "获取市场数据失败", "data": []}
    
    def update_market_data(self, data: Dict[str, Any]):
        """更新市场数据
        
        Args:
            data: WebSocket市场数据
        """
        if not data:
            return
        
        # 解析WebSocket数据
        # 这里需要根据实际的WebSocket数据格式进行解析
        # 示例：data = {"instId": "BTC-USDT", "last": "60000.00", ...}
        
        inst_id = data.get("instId")
        if inst_id:
            self.market_data[inst_id] = data
            self.last_update_time[inst_id] = time.time()
    
    def get_all_market_data(self) -> Dict[str, Any]:
        """获取所有市场数据
        
        Returns:
            所有市场数据
        """
        return self.market_data
