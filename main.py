#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX交易机器人主程序
基于12层架构设计的加密货币交易自动化工具
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from trading_gui import TradingBotGUI
from okx_api_client import OKXAPIClient
from commons.event_bus import EventBus
from agents.market_data_agent import MarketDataAgent
from agents.order_agent import OrderAgent
from agents.risk_management_agent import RiskManagementAgent
from agents.strategy_execution_agent import StrategyExecutionAgent
from agents.decision_coordination_agent import DecisionCoordinationAgent
from commons.config_manager import ConfigManager

class TradingBot:
    def __init__(self):
        """初始化交易机器人"""
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 初始化事件总线
        self.event_bus = EventBus()
        
        # 初始化API客户端
        self.api_client = OKXAPIClient(
            api_key=self.config.get('api_key', ''),
            secret_key=self.config.get('secret_key', ''),
            passphrase=self.config.get('passphrase', ''),
            proxy=self.config.get('proxy', '')
        )
        
        # 初始化各个代理
        self.market_data_agent = MarketDataAgent(self.api_client, self.event_bus)
        self.order_agent = OrderAgent(self.api_client, self.event_bus)
        self.risk_management_agent = RiskManagementAgent(self.event_bus)
        self.strategy_execution_agent = StrategyExecutionAgent(self.event_bus)
        self.decision_coordination_agent = DecisionCoordinationAgent(self.event_bus)
        
        # 初始化GUI
        self.gui = None
    
    def start_gui(self):
        """启动GUI界面"""
        app = QApplication(sys.argv)
        self.gui = TradingBotGUI(self)
        self.gui.show()
        sys.exit(app.exec_())
    
    def start_agents(self):
        """启动所有代理"""
        self.market_data_agent.start()
        self.order_agent.start()
        self.risk_management_agent.start()
        self.strategy_execution_agent.start()
        self.decision_coordination_agent.start()
    
    def stop_agents(self):
        """停止所有代理"""
        self.market_data_agent.stop()
        self.order_agent.stop()
        self.risk_management_agent.stop()
        self.strategy_execution_agent.stop()
        self.decision_coordination_agent.stop()
    
    def run(self):
        """运行交易机器人"""
        try:
            # 启动代理
            self.start_agents()
            
            # 启动GUI
            self.start_gui()
        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            # 停止代理
            self.stop_agents()

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()