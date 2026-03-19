import asyncio
import websockets
import json
import hmac
import hashlib
import base64
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OKXWebsocketClient:
    def __init__(self, api_key: str, secret_key: str, passphrase: str, use_proxy: bool = False, proxy_url: str = None):
        """初始化OKX WebSocket客户端
        
        Args:
            api_key: OKX API密钥
            secret_key: OKX API密钥密码
            passphrase: OKX API密钥密码短语
            use_proxy: 是否使用代理
            proxy_url: 代理URL
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        
        # WebSocket URL
        self.public_ws_url = "wss://ws.okx.com:8443/ws/v5/public"
        self.private_ws_url = "wss://ws.okx.com:8443/ws/v5/private"
        
        # WebSocket连接
        self.public_ws = None
        self.private_ws = None
        
        # 回调函数
        self.public_callbacks = {}
        self.private_callbacks = {}
        
        # 订阅列表
        self.public_subscriptions = []
        self.private_subscriptions = []
        
        # 重连参数
        self.reconnect_interval = 5  # 重连间隔（秒）
        self.max_reconnect_attempts = 10  # 最大重连次数
        self.reconnect_attempts = 0
        
        # 状态
        self.running = False
        
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """生成签名
        
        Args:
            timestamp: 时间戳
            method: HTTP方法
            request_path: 请求路径
            body: 请求体
            
        Returns:
            签名
        """
        message = timestamp + method + request_path + body
        mac = hmac.new(bytes(self.secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode("utf-8")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳
        
        Returns:
            时间戳
        """
        return str(int(time.time() * 1000))
    
    async def _connect_public(self):
        """连接公共WebSocket"""
        try:
            if self.use_proxy and self.proxy_url:
                import socks
                import socket
                
                # 解析代理URL
                proxy_parts = self.proxy_url.split('://')[1].split(':')
                proxy_host = proxy_parts[0]
                proxy_port = int(proxy_parts[1])
                
                # 创建代理连接
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
                sock.connect(("ws.okx.com", 8443))
                
                # 使用sock创建websocket连接
                self.public_ws = await websockets.connect(
                    self.public_ws_url,
                    sock=sock
                )
            else:
                self.public_ws = await websockets.connect(self.public_ws_url)
            
            logger.info("公共WebSocket连接成功")
            self.reconnect_attempts = 0
            
            # 重新订阅
            for subscription in self.public_subscriptions:
                await self._send_public_subscription(subscription)
            
        except Exception as e:
            logger.error(f"公共WebSocket连接失败: {e}")
            self.reconnect_attempts += 1
            if self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"{self.reconnect_interval}秒后尝试重连...")
                await asyncio.sleep(self.reconnect_interval)
                await self._connect_public()
            else:
                logger.error("达到最大重连次数，停止尝试")
    
    async def _connect_private(self):
        """连接私有WebSocket"""
        try:
            if self.use_proxy and self.proxy_url:
                import socks
                import socket
                
                # 解析代理URL
                proxy_parts = self.proxy_url.split('://')[1].split(':')
                proxy_host = proxy_parts[0]
                proxy_port = int(proxy_parts[1])
                
                # 创建代理连接
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
                sock.connect(("ws.okx.com", 8443))
                
                # 使用sock创建websocket连接
                self.private_ws = await websockets.connect(
                    self.private_ws_url,
                    sock=sock
                )
            else:
                self.private_ws = await websockets.connect(self.private_ws_url)
            
            # 发送登录请求
            await self._send_login()
            
            logger.info("私有WebSocket连接成功")
            self.reconnect_attempts = 0
            
            # 重新订阅
            for subscription in self.private_subscriptions:
                await self._send_private_subscription(subscription)
            
        except Exception as e:
            logger.error(f"私有WebSocket连接失败: {e}")
            self.reconnect_attempts += 1
            if self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"{self.reconnect_interval}秒后尝试重连...")
                await asyncio.sleep(self.reconnect_interval)
                await self._connect_private()
            else:
                logger.error("达到最大重连次数，停止尝试")
    
    async def _send_login(self):
        """发送登录请求"""
        timestamp = self._get_timestamp()
        request_path = "/users/self/verify"
        body = ""
        signature = self._generate_signature(timestamp, "GET", request_path, body)
        
        login_data = {
            "op": "login",
            "args": [
                {
                    "apiKey": self.api_key,
                    "passphrase": self.passphrase,
                    "timestamp": timestamp,
                    "sign": signature
                }
            ]
        }
        
        await self.private_ws.send(json.dumps(login_data))
        
        # 接收登录响应
        response = await self.private_ws.recv()
        logger.info(f"登录响应: {response}")
    
    async def _send_public_subscription(self, subscription: Dict[str, Any]):
        """发送公共订阅请求
        
        Args:
            subscription: 订阅参数
        """
        if self.public_ws and not self.public_ws.closed:
            sub_data = {
                "op": "subscribe",
                "args": [subscription]
            }
            await self.public_ws.send(json.dumps(sub_data))
            logger.info(f"公共订阅: {subscription}")
    
    async def _send_private_subscription(self, subscription: Dict[str, Any]):
        """发送私有订阅请求
        
        Args:
            subscription: 订阅参数
        """
        if self.private_ws and not self.private_ws.closed:
            sub_data = {
                "op": "subscribe",
                "args": [subscription]
            }
            await self.private_ws.send(json.dumps(sub_data))
            logger.info(f"私有订阅: {subscription}")
    
    async def _handle_public_message(self, message: str):
        """处理公共WebSocket消息
        
        Args:
            message: 消息内容
        """
        try:
            data = json.loads(message)
            
            # 处理订阅数据
            if "data" in data:
                channel = data.get("arg", {}).get("channel")
                if channel in self.public_callbacks:
                    for callback in self.public_callbacks[channel]:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"公共回调执行失败: {e}")
        except Exception as e:
            logger.error(f"处理公共消息失败: {e}")
    
    async def _handle_private_message(self, message: str):
        """处理私有WebSocket消息
        
        Args:
            message: 消息内容
        """
        try:
            data = json.loads(message)
            
            # 处理订阅数据
            if "data" in data:
                channel = data.get("arg", {}).get("channel")
                if channel in self.private_callbacks:
                    for callback in self.private_callbacks[channel]:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"私有回调执行失败: {e}")
        except Exception as e:
            logger.error(f"处理私有消息失败: {e}")
    
    async def _public_listener(self):
        """公共WebSocket监听器"""
        while self.running:
            if not self.public_ws or self.public_ws.closed:
                await self._connect_public()
            
            try:
                message = await self.public_ws.recv()
                await self._handle_public_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("公共WebSocket连接关闭")
                await self._connect_public()
            except Exception as e:
                logger.error(f"公共WebSocket错误: {e}")
                await asyncio.sleep(1)
    
    async def _private_listener(self):
        """私有WebSocket监听器"""
        while self.running:
            if not self.private_ws or self.private_ws.closed:
                await self._connect_private()
            
            try:
                message = await self.private_ws.recv()
                await self._handle_private_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("私有WebSocket连接关闭")
                await self._connect_private()
            except Exception as e:
                logger.error(f"私有WebSocket错误: {e}")
                await asyncio.sleep(1)
    
    def subscribe_public(self, channel: str, inst_id: str, callback: Callable[[Dict[str, Any]], None]):
        """订阅公共数据
        
        Args:
            channel: 频道
            inst_id: 交易对
            callback: 回调函数
        """
        subscription = {
            "channel": channel,
            "instId": inst_id
        }
        
        # 添加到订阅列表
        if subscription not in self.public_subscriptions:
            self.public_subscriptions.append(subscription)
        
        # 添加回调
        if channel not in self.public_callbacks:
            self.public_callbacks[channel] = []
        if callback not in self.public_callbacks[channel]:
            self.public_callbacks[channel].append(callback)
        
        # 如果已经连接，立即发送订阅请求
        if self.public_ws and not self.public_ws.closed:
            asyncio.create_task(self._send_public_subscription(subscription))
    
    def subscribe_private(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """订阅私有数据
        
        Args:
            channel: 频道
            callback: 回调函数
        """
        subscription = {
            "channel": channel
        }
        
        # 添加到订阅列表
        if subscription not in self.private_subscriptions:
            self.private_subscriptions.append(subscription)
        
        # 添加回调
        if channel not in self.private_callbacks:
            self.private_callbacks[channel] = []
        if callback not in self.private_callbacks[channel]:
            self.private_callbacks[channel].append(callback)
        
        # 如果已经连接，立即发送订阅请求
        if self.private_ws and not self.private_ws.closed:
            asyncio.create_task(self._send_private_subscription(subscription))
    
    def unsubscribe_public(self, channel: str, inst_id: str):
        """取消订阅公共数据
        
        Args:
            channel: 频道
            inst_id: 交易对
        """
        subscription = {
            "channel": channel,
            "instId": inst_id
        }
        
        # 从订阅列表中移除
        if subscription in self.public_subscriptions:
            self.public_subscriptions.remove(subscription)
        
        # 发送取消订阅请求
        if self.public_ws and not self.public_ws.closed:
            unsub_data = {
                "op": "unsubscribe",
                "args": [subscription]
            }
            asyncio.create_task(self.public_ws.send(json.dumps(unsub_data)))
    
    def unsubscribe_private(self, channel: str):
        """取消订阅私有数据
        
        Args:
            channel: 频道
        """
        subscription = {
            "channel": channel
        }
        
        # 从订阅列表中移除
        if subscription in self.private_subscriptions:
            self.private_subscriptions.remove(subscription)
        
        # 发送取消订阅请求
        if self.private_ws and not self.private_ws.closed:
            unsub_data = {
                "op": "unsubscribe",
                "args": [subscription]
            }
            asyncio.create_task(self.private_ws.send(json.dumps(unsub_data)))
    
    async def start(self):
        """启动WebSocket客户端"""
        self.running = True
        
        # 启动公共和私有WebSocket监听器
        public_task = asyncio.create_task(self._public_listener())
        private_task = asyncio.create_task(self._private_listener())
        
        return public_task, private_task
    
    async def stop(self):
        """停止WebSocket客户端"""
        self.running = False
        
        # 关闭WebSocket连接
        if self.public_ws and not self.public_ws.closed:
            await self.public_ws.close()
        
        if self.private_ws and not self.private_ws.closed:
            await self.private_ws.close()
        
        logger.info("WebSocket客户端已停止")
