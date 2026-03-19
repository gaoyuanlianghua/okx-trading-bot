from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyExecutionAgent(BaseAgent):
    """策略执行代理"""
    
    def __init__(self, trading_bot):
        """初始化策略执行代理
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__("StrategyExecutionAgent")
        self.trading_bot = trading_bot
        self.current_strategy = None
        self.strategy_params = {}
        self.last_execution_time = 0
        
    def start(self):
        """启动代理"""
        self.running = True
        self.log("策略执行代理启动")
        
    def stop(self):
        """停止代理"""
        self.running = False
        self.log("策略执行代理停止")
    
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.running:
            return None
        
        # 处理策略启动请求
        if data.get("type") == "start_strategy":
            return self.start_strategy(data)
        
        # 处理策略停止请求
        elif data.get("type") == "stop_strategy":
            return self.stop_strategy(data)
        
        # 处理策略更新请求
        elif data.get("type") == "update_strategy":
            return self.update_strategy(data)
        
        # 处理策略执行请求
        elif data.get("type") == "execute_strategy":
            return self.execute_strategy(data)
        
        return None
    
    def start_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """启动策略
        
        Args:
            data: 策略启动参数
            
        Returns:
            启动结果
        """
        strategy_name = data.get("strategy_name")
        params = data.get("params", {})
        
        if strategy_name:
            self.current_strategy = strategy_name
            self.strategy_params = params
            self.last_execution_time = time.time()
            
            self.log(f"策略启动: {strategy_name}, 参数: {params}")
            return {
                "code": "0",
                "msg": f"策略启动成功: {strategy_name}",
                "data": [{"strategy": strategy_name, "params": params}]
            }
        else:
            return {
                "code": "400",
                "msg": "策略名称不能为空",
                "data": []
            }
    
    def stop_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """停止策略
        
        Args:
            data: 策略停止参数
            
        Returns:
            停止结果
        """
        strategy_name = data.get("strategy_name")
        
        if self.current_strategy:
            stopped_strategy = self.current_strategy
            self.current_strategy = None
            self.strategy_params = {}
            
            self.log(f"策略停止: {stopped_strategy}")
            return {
                "code": "0",
                "msg": f"策略停止成功: {stopped_strategy}",
                "data": [{"strategy": stopped_strategy, "status": "stopped"}]
            }
        else:
            return {
                "code": "400",
                "msg": "没有正在运行的策略",
                "data": []
            }
    
    def update_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新策略参数
        
        Args:
            data: 策略更新参数
            
        Returns:
            更新结果
        """
        strategy_name = data.get("strategy_name")
        params = data.get("params", {})
        
        if self.current_strategy and self.current_strategy == strategy_name:
            self.strategy_params.update(params)
            
            self.log(f"策略参数更新: {strategy_name}, 新参数: {self.strategy_params}")
            return {
                "code": "0",
                "msg": f"策略参数更新成功: {strategy_name}",
                "data": [{"strategy": strategy_name, "params": self.strategy_params}]
            }
        else:
            return {
                "code": "400",
                "msg": "策略未运行或名称不匹配",
                "data": []
            }
    
    def execute_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略
        
        Args:
            data: 策略执行参数
            
        Returns:
            执行结果
        """
        if not self.current_strategy:
            return {
                "code": "400",
                "msg": "没有正在运行的策略",
                "data": []
            }
        
        # 检查执行间隔
        current_time = time.time()
        execution_interval = self.strategy_params.get("execution_interval", 60)  # 默认60秒
        
        if current_time - self.last_execution_time < execution_interval:
            return {
                "code": "429",
                "msg": f"策略执行过于频繁，请等待 {execution_interval} 秒",
                "data": []
            }
        
        # 执行策略
        try:
            result = self._execute_current_strategy()
            self.last_execution_time = current_time
            return result
        except Exception as e:
            self.error(f"策略执行失败: {e}")
            return {
                "code": "500",
                "msg": f"策略执行失败: {e}",
                "data": []
            }
    
    def _execute_current_strategy(self) -> Dict[str, Any]:
        """执行当前策略
        
        Returns:
            执行结果
        """
        if self.current_strategy == "dynamic":
            return self._execute_dynamic_strategy()
        elif self.current_strategy == "passivbot":
            return self._execute_passivbot_strategy()
        else:
            return {
                "code": "400",
                "msg": f"未知策略: {self.current_strategy}",
                "data": []
            }
    
    def _execute_dynamic_strategy(self) -> Dict[str, Any]:
        """执行动态策略
        
        Returns:
            执行结果
        """
        # 这里实现动态策略的执行逻辑
        # 例如：基于市场数据进行交易决策
        
        inst_id = self.strategy_params.get("inst_id", "BTC-USDT")
        amount = self.strategy_params.get("amount", "0.001")
        
        # 示例：随机决定买卖方向
        import random
        side = random.choice(["buy", "sell"])
        
        # 构建交易请求
        trade_request = {
            "type": "trade_request",
            "inst_id": inst_id,
            "side": side,
            "pos_side": "long",
            "ord_type": "market",
            "sz": amount
        }
        
        # 发送交易请求
        if self.trading_bot:
            return self.trading_bot.process_trade_request(trade_request)
        
        return {
            "code": "500",
            "msg": "交易机器人未初始化",
            "data": []
        }
    
    def _execute_passivbot_strategy(self) -> Dict[str, Any]:
        """执行PassivBot策略
        
        Returns:
            执行结果
        """
        # 这里实现PassivBot策略的执行逻辑
        # 例如：调用PassivBot集成模块
        
        if self.trading_bot and hasattr(self.trading_bot, "passivbot_integrator"):
            try:
                result = self.trading_bot.passivbot_integrator.execute()
                return {
                    "code": "0",
                    "msg": "PassivBot策略执行成功",
                    "data": [result]
                }
            except Exception as e:
                self.error(f"PassivBot策略执行失败: {e}")
                return {
                    "code": "500",
                    "msg": f"PassivBot策略执行失败: {e}",
                    "data": []
                }
        
        return {
            "code": "500",
            "msg": "PassivBot集成未初始化",
            "data": []
        }
    
    def get_current_strategy(self) -> Dict[str, Any]:
        """获取当前策略
        
        Returns:
            当前策略信息
        """
        if self.current_strategy:
            return {
                "strategy": self.current_strategy,
                "params": self.strategy_params,
                "last_execution": self.last_execution_time
            }
        else:
            return {
                "strategy": None,
                "params": {},
                "last_execution": 0
            }
