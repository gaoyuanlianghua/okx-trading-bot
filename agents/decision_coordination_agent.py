from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DecisionCoordinationAgent(BaseAgent):
    """决策协调代理"""
    
    def __init__(self, trading_bot):
        """初始化决策协调代理
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__("DecisionCoordinationAgent")
        self.trading_bot = trading_bot
        self.agents = {}
        
    def start(self):
        """启动代理"""
        self.running = True
        self.log("决策协调代理启动")
        
    def stop(self):
        """停止代理"""
        self.running = False
        self.log("决策协调代理停止")
        
    def register_agent(self, agent_name: str, agent):
        """注册代理
        
        Args:
            agent_name: 代理名称
            agent: 代理实例
        """
        self.agents[agent_name] = agent
        self.log(f"代理注册: {agent_name}")
    
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        if not self.running:
            return None
        
        # 处理交易请求
        if data.get("type") == "trade_request":
            return self.handle_trade_request(data)
        
        # 处理策略执行请求
        elif data.get("type") == "strategy_execution":
            return self.handle_strategy_execution(data)
        
        # 处理状态查询请求
        elif data.get("type") == "status_query":
            return self.handle_status_query(data)
        
        return None
    
    def handle_trade_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理交易请求
        
        Args:
            data: 交易请求数据
            
        Returns:
            处理结果
        """
        # 1. 风险评估
        risk_agent = self.agents.get("RiskManagementAgent")
        if risk_agent:
            risk_result = risk_agent.process({
                "type": "risk_evaluation",
                "inst_id": data.get("inst_id"),
                "sz": data.get("sz"),
                "side": data.get("side"),
                "pos_side": data.get("pos_side")
            })
            
            if not risk_result.get("approved"):
                self.log(f"交易被风险控制拒绝: {risk_result.get('reason')}")
                return {
                    "code": "400",
                    "msg": f"交易被风险控制拒绝: {risk_result.get('reason')}",
                    "data": []
                }
        
        # 2. 市场数据获取
        market_agent = self.agents.get("MarketDataAgent")
        if market_agent:
            market_data = market_agent.process({
                "type": "market_data_request",
                "inst_id": data.get("inst_id")
            })
            
            if not market_data or market_data.get("code") != "0":
                self.log("获取市场数据失败")
                return {
                    "code": "500",
                    "msg": "获取市场数据失败",
                    "data": []
                }
        
        # 3. 下单
        order_agent = self.agents.get("OrderAgent")
        if order_agent:
            order_result = order_agent.process({
                "type": "place_order",
                "inst_id": data.get("inst_id"),
                "side": data.get("side"),
                "pos_side": data.get("pos_side"),
                "ord_type": data.get("ord_type"),
                "sz": data.get("sz"),
                "px": data.get("px"),
                "tgt_ccy": data.get("tgt_ccy"),
                "cl_ord_id": data.get("cl_ord_id")
            })
            
            # 4. 记录交易
            if risk_agent and order_result and order_result.get("code") == "0":
                risk_agent.record_trade(order_result)
            
            return order_result
        
        return {
            "code": "500",
            "msg": "订单代理未初始化",
            "data": []
        }
    
    def handle_strategy_execution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理策略执行请求
        
        Args:
            data: 策略执行数据
            
        Returns:
            处理结果
        """
        strategy_name = data.get("strategy_name")
        action = data.get("action")  # start or stop
        
        if action == "start":
            # 启动策略
            if self.trading_bot:
                try:
                    if strategy_name == "dynamic":
                        self.trading_bot.start_dynamic_strategy()
                    elif strategy_name == "passivbot":
                        self.trading_bot.start_passivbot_strategy()
                    
                    self.log(f"策略启动: {strategy_name}")
                    return {
                        "code": "0",
                        "msg": "策略启动成功",
                        "data": [{"strategy": strategy_name, "status": "running"}]
                    }
                except Exception as e:
                    self.error(f"策略启动失败: {e}")
                    return {
                        "code": "500",
                        "msg": f"策略启动失败: {e}",
                        "data": []
                    }
        
        elif action == "stop":
            # 停止策略
            if self.trading_bot:
                try:
                    self.trading_bot.stop_strategy()
                    self.log(f"策略停止: {strategy_name}")
                    return {
                        "code": "0",
                        "msg": "策略停止成功",
                        "data": [{"strategy": strategy_name, "status": "stopped"}]
                    }
                except Exception as e:
                    self.error(f"策略停止失败: {e}")
                    return {
                        "code": "500",
                        "msg": f"策略停止失败: {e}",
                        "data": []
                    }
        
        return {
            "code": "400",
            "msg": "无效的策略操作",
            "data": []
        }
    
    def handle_status_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态查询请求
        
        Args:
            data: 状态查询数据
            
        Returns:
            处理结果
        """
        status_type = data.get("status_type")
        
        if status_type == "agents":
            # 获取代理状态
            agent_status = {}
            for agent_name, agent in self.agents.items():
                agent_status[agent_name] = "running" if agent.running else "stopped"
            
            return {
                "code": "0",
                "msg": "",
                "data": [{"agents": agent_status}]
            }
        
        elif status_type == "risk":
            # 获取风险状态
            risk_agent = self.agents.get("RiskManagementAgent")
            if risk_agent:
                return {
                    "code": "0",
                    "msg": "",
                    "data": [{
                        "risk_params": risk_agent.get_risk_params(),
                        "trade_stats": risk_agent.get_trade_stats()
                    }]
                }
        
        return {
            "code": "400",
            "msg": "无效的状态查询类型",
            "data": []
        }
    
    def get_agents(self) -> Dict[str, Any]:
        """获取所有代理
        
        Returns:
            代理字典
        """
        return self.agents
