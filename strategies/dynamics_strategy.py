from .base_strategy import BaseStrategy
from typing import Dict, Any, Optional
import logging
import time
import random
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicsStrategy(BaseStrategy):
    """动态策略"""
    
    def __init__(self, trading_bot):
        """初始化动态策略
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__(trading_bot)
        self.name = "DynamicsStrategy"
        self.inst_id = "BTC-USDT"
        self.last_trade_time = 0
        self.trade_interval = 60  # 交易间隔（秒）
        self.amount = "0.001"  # 交易数量
        
    def start(self):
        """启动策略"""
        self.running = True
        self.log("策略启动")
        
    def stop(self):
        """停止策略"""
        self.running = False
        self.log("策略停止")
        
    def update(self, market_data: Dict[str, Any]):
        """更新策略
        
        Args:
            market_data: 市场数据
        """
        if not self.running:
            return
        
        current_time = time.time()
        if current_time - self.last_trade_time < self.trade_interval:
            return
        
        # 获取市场数据
        ticker_data = self.get_market_data(self.inst_id)
        if not ticker_data or ticker_data.get("code") != "0":
            self.log("获取市场数据失败")
            return
        
        # 解析市场数据
        data = ticker_data.get("data", [])
        if not data:
            self.log("市场数据为空")
            return
        
        ticker = data[0]
        last_price = float(ticker.get("last", "0"))
        
        # 随机决定买卖方向
        side = random.choice(["buy", "sell"])
        
        # 限价单价格
        if side == "buy":
            price = str(last_price * 0.999)  # 稍微低于当前价格
        else:
            price = str(last_price * 1.001)  # 稍微高于当前价格
        
        # 下单
        try:
            result = self.place_order(
                inst_id=self.inst_id,
                side=side,
                pos_side="long",
                ord_type="limit",
                sz=self.amount,
                px=price
            )
            
            if result and result.get("code") == "0":
                self.log(f"下单成功: {side} {self.inst_id} {self.amount} @ {price}")
                self.last_trade_time = current_time
            else:
                self.log(f"下单失败: {result}")
        except Exception as e:
            self.log(f"下单异常: {e}")
