from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskManagementAgent(BaseAgent):
    """风险管理代理"""
    
    def __init__(self, trading_bot):
        """初始化风险管理代理
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__("RiskManagementAgent")
        self.trading_bot = trading_bot
        
        # 风险参数
        self.risk_params = {
            "max_position_size": 0.1,  # 最大持仓大小（BTC）
            "max_leverage": 10,  # 最大杠杆
            "max_loss_per_trade": 0.001,  # 每笔交易最大亏损（BTC）
            "max_daily_loss": 0.005,  # 每日最大亏损（BTC）
            "max_trades_per_hour": 10,  # 每小时最大交易次数
            "min_order_size": 0.0001,  # 最小订单大小（BTC）
            "max_order_size": 0.01,  # 最大订单大小（BTC）
        }
        
        # 交易统计
        self.trade_stats = {
            "today_trades": 0,
            "today_loss": 0,
            "hour_trades": 0,
            "last_hour": datetime.now().hour
        }
        
    def start(self):
        """启动代理"""
        self.running = True
        self.log("风险管理代理启动")
        
    def stop(self):
        """停止代理"""
        self.running = False
        self.log("风险管理代理停止")
        
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.running:
            return None
        
        # 处理风险评估请求
        if data.get("type") == "risk_evaluation":
            return self.evaluate_risk(data)
        
        # 处理风险参数更新请求
        elif data.get("type") == "update_risk_params":
            return self.update_risk_params(data)
        
        return None
    
    def evaluate_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险
        
        Args:
            data: 交易参数
            
        Returns:
            风险评估结果
        """
        # 检查交易频率
        self._update_trade_stats()
        if self.trade_stats["hour_trades"] >= self.risk_params["max_trades_per_hour"]:
            return {
                "approved": False,
                "reason": f"每小时交易次数超过限制: {self.trade_stats['hour_trades']}/{self.risk_params['max_trades_per_hour']}"
            }
        
        # 检查订单大小
        sz = data.get("sz")
        if sz:
            try:
                sz = float(sz)
                if sz < self.risk_params["min_order_size"]:
                    return {
                        "approved": False,
                        "reason": f"订单大小低于最小限制: {sz} < {self.risk_params['min_order_size']}"
                    }
                if sz > self.risk_params["max_order_size"]:
                    return {
                        "approved": False,
                        "reason": f"订单大小超过最大限制: {sz} > {self.risk_params['max_order_size']}"
                    }
            except ValueError:
                return {
                    "approved": False,
                    "reason": "订单大小格式错误"
                }
        
        # 检查持仓大小
        position = self._get_current_position(data.get("inst_id"))
        if position:
            pos_sz = abs(float(position.get("pos", "0")))
            if pos_sz >= self.risk_params["max_position_size"]:
                return {
                    "approved": False,
                    "reason": f"持仓大小超过限制: {pos_sz} >= {self.risk_params['max_position_size']}"
                }
        
        # 检查每日亏损
        if self.trade_stats["today_loss"] >= self.risk_params["max_daily_loss"]:
            return {
                "approved": False,
                "reason": f"每日亏损超过限制: {self.trade_stats['today_loss']} >= {self.risk_params['max_daily_loss']}"
            }
        
        # 风险评估通过
        return {
            "approved": True,
            "reason": "风险评估通过"
        }
    
    def update_risk_params(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新风险参数
        
        Args:
            data: 新的风险参数
            
        Returns:
            更新结果
        """
        try:
            for key, value in data.get("params", {}).items():
                if key in self.risk_params:
                    self.risk_params[key] = value
            
            self.log(f"风险参数更新: {self.risk_params}")
            return {
                "success": True,
                "params": self.risk_params
            }
        except Exception as e:
            self.error(f"更新风险参数失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_trade_stats(self):
        """更新交易统计"""
        current_hour = datetime.now().hour
        if current_hour != self.trade_stats["last_hour"]:
            self.trade_stats["hour_trades"] = 0
            self.trade_stats["last_hour"] = current_hour
        
        # 每日重置
        current_date = datetime.now().date()
        if hasattr(self, "last_date"):
            if current_date != self.last_date:
                self.trade_stats["today_trades"] = 0
                self.trade_stats["today_loss"] = 0
        self.last_date = current_date
    
    def _get_current_position(self, inst_id: str) -> Optional[Dict[str, Any]]:
        """获取当前持仓
        
        Args:
            inst_id: 交易对
            
        Returns:
            持仓信息
        """
        if not self.trading_bot:
            return None
        
        try:
            position_data = self.trading_bot.get_position(inst_id)
            if position_data and position_data.get("code") == "0":
                data = position_data.get("data", [])
                if data:
                    return data[0]
        except Exception as e:
            self.error(f"获取持仓信息失败: {e}")
        
        return None
    
    def record_trade(self, trade_result: Dict[str, Any]):
        """记录交易
        
        Args:
            trade_result: 交易结果
        """
        self.trade_stats["today_trades"] += 1
        self.trade_stats["hour_trades"] += 1
        
        # 这里可以添加亏损计算逻辑
    
    def get_risk_params(self) -> Dict[str, Any]:
        """获取风险参数
        
        Returns:
            风险参数
        """
        return self.risk_params
    
    def get_trade_stats(self) -> Dict[str, Any]:
        """获取交易统计
        
        Returns:
            交易统计
        """
        return self.trade_stats
