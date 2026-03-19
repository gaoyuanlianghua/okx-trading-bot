import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
                            QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox, 
                            QGridLayout, QScrollArea, QSplitter, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingGUI(QMainWindow):
    def __init__(self, trading_bot=None):
        """初始化交易GUI
        
        Args:
            trading_bot: 交易机器人实例
        """
        super().__init__()
        self.trading_bot = trading_bot
        self.init_ui()
        self.init_signals()
        self.init_timers()
    
    def init_ui(self):
        """初始化UI"""
        # 设置窗口
        self.setWindowTitle("OKX交易机器人")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 顶部状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 交易面板
        self.trade_tab = QWidget()
        self.init_trade_tab()
        
        # 市场数据面板
        self.market_tab = QWidget()
        self.init_market_tab()
        
        # 账户面板
        self.account_tab = QWidget()
        self.init_account_tab()
        
        # 订单面板
        self.order_tab = QWidget()
        self.init_order_tab()
        
        # 策略面板
        self.strategy_tab = QWidget()
        self.init_strategy_tab()
        
        # 日志面板
        self.log_tab = QWidget()
        self.init_log_tab()
        
        # 添加标签页
        self.tab_widget.addTab(self.trade_tab, "交易")
        self.tab_widget.addTab(self.market_tab, "市场")
        self.tab_widget.addTab(self.account_tab, "账户")
        self.tab_widget.addTab(self.order_tab, "订单")
        self.tab_widget.addTab(self.strategy_tab, "策略")
        self.tab_widget.addTab(self.log_tab, "日志")
        
        main_layout.addWidget(self.tab_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def init_trade_tab(self):
        """初始化交易面板"""
        layout = QVBoxLayout()
        
        # 交易对选择
        pair_layout = QHBoxLayout()
        pair_label = QLabel("交易对:")
        self.pair_combo = QComboBox()
        # 添加常见交易对
        self.pair_combo.addItems(["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        pair_layout.addWidget(pair_label)
        pair_layout.addWidget(self.pair_combo)
        
        # 交易参数
        param_group = QGroupBox("交易参数")
        param_layout = QGridLayout()
        
        # 方向
        direction_label = QLabel("方向:")
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["买入", "卖出"])
        param_layout.addWidget(direction_label, 0, 0)
        param_layout.addWidget(self.direction_combo, 0, 1)
        
        # 持仓方向
        pos_side_label = QLabel("持仓方向:")
        self.pos_side_combo = QComboBox()
        self.pos_side_combo.addItems(["多头", "空头"])
        param_layout.addWidget(pos_side_label, 0, 2)
        param_layout.addWidget(self.pos_side_combo, 0, 3)
        
        # 订单类型
        ord_type_label = QLabel("订单类型:")
        self.ord_type_combo = QComboBox()
        self.ord_type_combo.addItems(["限价", "市价"])
        param_layout.addWidget(ord_type_label, 1, 0)
        param_layout.addWidget(self.ord_type_combo, 1, 1)
        
        # 价格
        price_label = QLabel("价格:")
        self.price_edit = QLineEdit()
        param_layout.addWidget(price_label, 1, 2)
        param_layout.addWidget(self.price_edit, 1, 3)
        
        # 数量
        amount_label = QLabel("数量:")
        self.amount_edit = QLineEdit()
        param_layout.addWidget(amount_label, 2, 0)
        param_layout.addWidget(self.amount_edit, 2, 1)
        
        # 百分比
        percent_label = QLabel("百分比:")
        self.percent_combo = QComboBox()
        self.percent_combo.addItems(["10%", "25%", "50%", "75%", "100%"])
        param_layout.addWidget(percent_label, 2, 2)
        param_layout.addWidget(self.percent_combo, 2, 3)
        
        param_group.setLayout(param_layout)
        
        # 交易按钮
        button_layout = QHBoxLayout()
        self.buy_button = QPushButton("买入")
        self.sell_button = QPushButton("卖出")
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.buy_button)
        button_layout.addWidget(self.sell_button)
        button_layout.addWidget(self.cancel_button)
        
        # 交易结果
        self.trade_result = QTextEdit()
        self.trade_result.setReadOnly(True)
        
        layout.addLayout(pair_layout)
        layout.addWidget(param_group)
        layout.addLayout(button_layout)
        layout.addWidget(self.trade_result)
        
        self.trade_tab.setLayout(layout)
    
    def init_market_tab(self):
        """初始化市场数据面板"""
        layout = QVBoxLayout()
        
        # 市场数据表格
        self.market_table = QTableWidget()
        self.market_table.setColumnCount(6)
        self.market_table.setHorizontalHeaderLabels(["交易对", "最新价", "24h涨跌幅", "24h成交量", "最高价", "最低价"])
        
        # 添加示例数据
        self.update_market_data()
        
        layout.addWidget(self.market_table)
        self.market_tab.setLayout(layout)
    
    def init_account_tab(self):
        """初始化账户面板"""
        layout = QVBoxLayout()
        
        # 账户余额
        balance_group = QGroupBox("账户余额")
        balance_layout = QVBoxLayout()
        
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(3)
        self.balance_table.setHorizontalHeaderLabels(["币种", "可用余额", "总余额"])
        
        # 添加示例数据
        self.update_balance_data()
        
        balance_layout.addWidget(self.balance_table)
        balance_group.setLayout(balance_layout)
        
        # 持仓信息
        position_group = QGroupBox("持仓信息")
        position_layout = QVBoxLayout()
        
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels(["交易对", "持仓方向", "持仓数量", "平均成本", "浮动盈亏"])
        
        # 添加示例数据
        self.update_position_data()
        
        position_layout.addWidget(self.position_table)
        position_group.setLayout(position_layout)
        
        layout.addWidget(balance_group)
        layout.addWidget(position_group)
        self.account_tab.setLayout(layout)
    
    def init_order_tab(self):
        """初始化订单面板"""
        layout = QVBoxLayout()
        
        # 订单表格
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels(["订单ID", "交易对", "方向", "价格", "数量", "状态"])
        
        # 添加示例数据
        self.update_order_data()
        
        layout.addWidget(self.order_table)
        self.order_tab.setLayout(layout)
    
    def init_strategy_tab(self):
        """初始化策略面板"""
        layout = QVBoxLayout()
        
        # 策略选择
        strategy_layout = QHBoxLayout()
        strategy_label = QLabel("策略:")
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["动态策略", "PassivBot策略"])
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_combo)
        
        # 策略参数
        param_group = QGroupBox("策略参数")
        param_layout = QGridLayout()
        
        # 动态策略参数
        # 这里可以根据具体策略添加参数
        
        param_group.setLayout(param_layout)
        
        # 策略控制
        control_layout = QHBoxLayout()
        self.start_strategy_button = QPushButton("启动策略")
        self.stop_strategy_button = QPushButton("停止策略")
        control_layout.addWidget(self.start_strategy_button)
        control_layout.addWidget(self.stop_strategy_button)
        
        # 策略状态
        self.strategy_status = QLabel("策略状态: 未启动")
        
        layout.addLayout(strategy_layout)
        layout.addWidget(param_group)
        layout.addLayout(control_layout)
        layout.addWidget(self.strategy_status)
        
        self.strategy_tab.setLayout(layout)
    
    def init_log_tab(self):
        """初始化日志面板"""
        layout = QVBoxLayout()
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        layout.addWidget(self.log_text)
        self.log_tab.setLayout(layout)
    
    def init_signals(self):
        """初始化信号"""
        # 交易按钮
        self.buy_button.clicked.connect(self.on_buy_clicked)
        self.sell_button.clicked.connect(self.on_sell_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        
        # 策略按钮
        self.start_strategy_button.clicked.connect(self.on_start_strategy)
        self.stop_strategy_button.clicked.connect(self.on_stop_strategy)
    
    def init_timers(self):
        """初始化定时器"""
        # 市场数据更新定时器
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_data)
        self.market_timer.start(5000)  # 每5秒更新一次
        
        # 账户数据更新定时器
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_data)
        self.account_timer.start(10000)  # 每10秒更新一次
        
        # 订单数据更新定时器
        self.order_timer = QTimer()
        self.order_timer.timeout.connect(self.update_order_data)
        self.order_timer.start(5000)  # 每5秒更新一次
    
    def on_buy_clicked(self):
        """买入按钮点击事件"""
        pair = self.pair_combo.currentText().replace("/", "-")
        amount = self.amount_edit.text()
        price = self.price_edit.text()
        ord_type = self.ord_type_combo.currentText()
        
        if not amount:
            self.trade_result.append("请输入数量")
            return
        
        # 调用交易机器人下单
        if self.trading_bot:
            try:
                result = self.trading_bot.place_order(
                    inst_id=pair,
                    side="buy",
                    pos_side="long" if self.pos_side_combo.currentText() == "多头" else "short",
                    ord_type="limit" if ord_type == "限价" else "market",
                    sz=amount,
                    px=price if ord_type == "限价" else None
                )
                self.trade_result.append(f"买入订单已提交: {json.dumps(result, indent=2)}")
            except Exception as e:
                self.trade_result.append(f"下单失败: {e}")
        else:
            self.trade_result.append("交易机器人未初始化")
    
    def on_sell_clicked(self):
        """卖出按钮点击事件"""
        pair = self.pair_combo.currentText().replace("/", "-")
        amount = self.amount_edit.text()
        price = self.price_edit.text()
        ord_type = self.ord_type_combo.currentText()
        
        if not amount:
            self.trade_result.append("请输入数量")
            return
        
        # 调用交易机器人下单
        if self.trading_bot:
            try:
                result = self.trading_bot.place_order(
                    inst_id=pair,
                    side="sell",
                    pos_side="long" if self.pos_side_combo.currentText() == "多头" else "short",
                    ord_type="limit" if ord_type == "限价" else "market",
                    sz=amount,
                    px=price if ord_type == "限价" else None
                )
                self.trade_result.append(f"卖出订单已提交: {json.dumps(result, indent=2)}")
            except Exception as e:
                self.trade_result.append(f"下单失败: {e}")
        else:
            self.trade_result.append("交易机器人未初始化")
    
    def on_cancel_clicked(self):
        """取消按钮点击事件"""
        # 清空输入
        self.price_edit.clear()
        self.amount_edit.clear()
        self.trade_result.clear()
    
    def on_start_strategy(self):
        """启动策略"""
        strategy = self.strategy_combo.currentText()
        
        if self.trading_bot:
            try:
                if strategy == "动态策略":
                    self.trading_bot.start_dynamic_strategy()
                elif strategy == "PassivBot策略":
                    self.trading_bot.start_passivbot_strategy()
                self.strategy_status.setText("策略状态: 运行中")
                self.log_text.append(f"{datetime.now()} - 启动策略: {strategy}")
            except Exception as e:
                self.log_text.append(f"{datetime.now()} - 启动策略失败: {e}")
        else:
            self.log_text.append("交易机器人未初始化")
    
    def on_stop_strategy(self):
        """停止策略"""
        if self.trading_bot:
            try:
                self.trading_bot.stop_strategy()
                self.strategy_status.setText("策略状态: 已停止")
                self.log_text.append(f"{datetime.now()} - 停止策略")
            except Exception as e:
                self.log_text.append(f"{datetime.now()} - 停止策略失败: {e}")
        else:
            self.log_text.append("交易机器人未初始化")
    
    def update_market_data(self):
        """更新市场数据"""
        # 示例数据
        market_data = [
            ["BTC/USDT", "60000.00", "+2.5%", "12345.67", "61000.00", "59000.00"],
            ["ETH/USDT", "3000.00", "+1.8%", "9876.54", "3100.00", "2900.00"],
            ["BNB/USDT", "300.00", "-0.5%", "5432.10", "310.00", "290.00"],
            ["SOL/USDT", "100.00", "+3.2%", "8765.43", "105.00", "95.00"]
        ]
        
        self.market_table.setRowCount(len(market_data))
        for i, row in enumerate(market_data):
            for j, item in enumerate(row):
                self.market_table.setItem(i, j, QTableWidgetItem(item))
    
    def update_balance_data(self):
        """更新余额数据"""
        # 示例数据
        balance_data = [
            ["USDT", "10000.00", "10000.00"],
            ["BTC", "0.1", "0.1"],
            ["ETH", "1.0", "1.0"]
        ]
        
        self.balance_table.setRowCount(len(balance_data))
        for i, row in enumerate(balance_data):
            for j, item in enumerate(row):
                self.balance_table.setItem(i, j, QTableWidgetItem(item))
    
    def update_position_data(self):
        """更新持仓数据"""
        # 示例数据
        position_data = [
            ["BTC/USDT", "多头", "0.01", "58000.00", "+200.00"],
            ["ETH/USDT", "空头", "0.1", "3100.00", "+10.00"]
        ]
        
        self.position_table.setRowCount(len(position_data))
        for i, row in enumerate(position_data):
            for j, item in enumerate(row):
                self.position_table.setItem(i, j, QTableWidgetItem(item))
    
    def update_account_data(self):
        """更新账户数据"""
        self.update_balance_data()
        self.update_position_data()
    
    def update_order_data(self):
        """更新订单数据"""
        # 示例数据
        order_data = [
            ["123456789", "BTC/USDT", "买入", "59000.00", "0.01", "已成交"],
            ["987654321", "ETH/USDT", "卖出", "3050.00", "0.5", "已挂单"]
        ]
        
        self.order_table.setRowCount(len(order_data))
        for i, row in enumerate(order_data):
            for j, item in enumerate(row):
                self.order_table.setItem(i, j, QTableWidgetItem(item))
    
    def add_log(self, message):
        """添加日志
        
        Args:
            message: 日志消息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def update_status(self, message):
        """更新状态栏
        
        Args:
            message: 状态栏消息
        """
        self.status_bar.showMessage(message, 3000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = TradingGUI()
    gui.show()
    sys.exit(app.exec_())
