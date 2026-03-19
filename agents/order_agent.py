from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrderAgent(BaseAgent):
    """订单代理"""
    
    def __init__(self, trading_bot):
        """初始化订单代理
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__("OrderAgent")
        self.trading_bot = trading_bot
        self.order_history = []
        
    def start(self):
        """启动代理"""
        self.running = True
        self.log("订单代理启动")
        
    def stop(self):
        """停止代理"""
        self.running = False
        self.log("订单代理停止")
        
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.running:
            return None
        
        # 处理下单请求
        if data.get("type") == "place_order":
            return self.place_order(data)
        
        # 处理撤单请求
        elif data.get("type") == "cancel_order":
            return self.cancel_order(data)
        
        # 处理获取订单请求
        elif data.get("type") == "get_order":
            return self.get_order(data)
        
        # 处理获取订单列表请求
        elif data.get("type") == "get_order_list":
            return self.get_order_list(data)
        
        return None
    
    def place_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """下单
        
        Args:
            data: 下单参数
            
        Returns:
            下单结果
        """
        if not self.trading_bot:
            return {"code": "500", "msg": "交易机器人未初始化", "data": []}
        
        try:
            result = self.trading_bot.place_order(
                inst_id=data.get("inst_id"),
                side=data.get("side"),
                pos_side=data.get("pos_side"),
                ord_type=data.get("ord_type"),
                sz=data.get("sz"),
                px=data.get("px"),
                tgt_ccy=data.get("tgt_ccy"),
                cl_ord_id=data.get("cl_ord_id")
            )
            
            if result and result.get("code") == "0":
                # 记录订单历史
                order_info = {
                    "order_id": result.get("data", [{}])[0].get("ordId"),
                    "inst_id": data.get("inst_id"),
                    "side": data.get("side"),
                    "pos_side": data.get("pos_side"),
                    "ord_type": data.get("ord_type"),
                    "sz": data.get("sz"),
                    "px": data.get("px"),
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending"
                }
                self.order_history.append(order_info)
                
                self.log(f"下单成功: {order_info}")
            else:
                self.error(f"下单失败: {result}")
            
            return result
        except Exception as e:
            self.error(f"下单异常: {e}")
            return {"code": "500", "msg": f"下单异常: {e}", "data": []}
    
    def cancel_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """撤单
        
        Args:
            data: 撤单参数
            
        Returns:
            撤单结果
        """
        if not self.trading_bot:
            return {"code": "500", "msg": "交易机器人未初始化", "data": []}
        
        try:
            result = self.trading_bot.cancel_order(
                inst_id=data.get("inst_id"),
                ord_id=data.get("ord_id"),
                cl_ord_id=data.get("cl_ord_id")
            )
            
            if result and result.get("code") == "0":
                self.log(f"撤单成功: {data}")
            else:
                self.error(f"撤单失败: {result}")
            
            return result
        except Exception as e:
            self.error(f"撤单异常: {e}")
            return {"code": "500", "msg": f"撤单异常: {e}", "data": []}
    
    def get_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取订单信息
        
        Args:
            data: 获取订单参数
            
        Returns:
            订单信息
        """
        if not self.trading_bot:
            return {"code": "500", "msg": "交易机器人未初始化", "data": []}
        
        try:
            result = self.trading_bot.get_order(
                inst_id=data.get("inst_id"),
                ord_id=data.get("ord_id"),
                cl_ord_id=data.get("cl_ord_id")
            )
            return result
        except Exception as e:
            self.error(f"获取订单信息异常: {e}")
            return {"code": "500", "msg": f"获取订单信息异常: {e}", "data": []}
    
    def get_order_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取订单列表
        
        Args:
            data: 获取订单列表参数
            
        Returns:
            订单列表
        """
        if not self.trading_bot:
            return {"code": "500", "msg": "交易机器人未初始化", "data": []}
        
        try:
            result = self.trading_bot.get_order_list(
                inst_id=data.get("inst_id"),
                ord_type=data.get("ord_type"),
                state=data.get("state"),
                after=data.get("after"),
                before=data.get("before"),
                limit=data.get("limit")
            )
            return result
        except Exception as e:
            self.error(f"获取订单列表异常: {e}")
            return {"code": "500", "msg": f"获取订单列表异常: {e}", "data": []}
    
    def get_order_history(self) -> list:
        """获取订单历史
        
        Returns:
            订单历史
        """
        return self.order_history
