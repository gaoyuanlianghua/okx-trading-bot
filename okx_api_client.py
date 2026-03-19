import hmac
import hashlib
import base64
import time
import requests
import json
import logging
from datetime import datetime
import random
import socket
import dns.resolver
import threading
from typing import Dict, Any, Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OKXAPIClient:
    def __init__(self, api_key: str, secret_key: str, passphrase: str, use_proxy: bool = False, proxy_url: str = None):
        """初始化OKX API客户端
        
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
        self.base_url = "https://www.okx.com"
        self.session = requests.Session()
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        
        # 配置代理
        if self.use_proxy and self.proxy_url:
            proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url
            }
            self.session.proxies = proxies
        
        # 配置会话参数
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 记录DNS解析结果
        self.dns_cache = {}
        self.dns_stats = {
            "resolved_count": 0,
            "failed_count": 0,
            "last_resolved": None
        }
        
        # 记录API调用统计
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_call": None
        }
        
        # 记录网络错误
        self.network_errors = []
        
        # 初始化DNS解析器
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 10
    
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
    
    def _resolve_dns(self, domain: str) -> List[str]:
        """解析DNS
        
        Args:
            domain: 域名
            
        Returns:
            IP地址列表
        """
        try:
            if domain in self.dns_cache:
                return self.dns_cache[domain]
            
            answers = self.dns_resolver.resolve(domain, 'A')
            ips = [answer.address for answer in answers]
            self.dns_cache[domain] = ips
            self.dns_stats["resolved_count"] += 1
            self.dns_stats["last_resolved"] = datetime.now().isoformat()
            logger.info(f"DNS解析成功: {domain} -> {ips}")
            return ips
        except Exception as e:
            self.dns_stats["failed_count"] += 1
            logger.error(f"DNS解析失败: {domain}, 错误: {e}")
            # 缓存失败结果，避免频繁重试
            self.dns_cache[domain] = []
            return []
    
    def _choose_ip(self, domain: str) -> Optional[str]:
        """选择IP地址
        
        Args:
            domain: 域名
            
        Returns:
            IP地址
        """
        ips = self._resolve_dns(domain)
        if not ips:
            return None
        return random.choice(ips)
    
    def _make_request(self, method: str, request_path: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送请求
        
        Args:
            method: HTTP方法
            request_path: 请求路径
            params: URL参数
            data: 请求体
            
        Returns:
            响应数据
        """
        self.api_stats["total_calls"] += 1
        self.api_stats["last_call"] = datetime.now().isoformat()
        
        try:
            timestamp = self._get_timestamp()
            body = json.dumps(data) if data else ""
            signature = self._generate_signature(timestamp, method, request_path, body)
            
            headers = {
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.passphrase
            }
            
            url = self.base_url + request_path
            
            if method == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data, params=params, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            self.api_stats["successful_calls"] += 1
            logger.info(f"API调用成功: {method} {request_path}")
            return result
            
        except ConnectionResetError as e:
            self.api_stats["failed_calls"] += 1
            error_msg = f"连接被重置: {e}"
            self.network_errors.append({"time": datetime.now().isoformat(), "error": error_msg})
            logger.error(error_msg)
            return {"code": "500", "msg": error_msg, "data": []}
            
        except requests.exceptions.RequestException as e:
            self.api_stats["failed_calls"] += 1
            error_msg = f"请求失败: {e}"
            self.network_errors.append({"time": datetime.now().isoformat(), "error": error_msg})
            logger.error(error_msg)
            return {"code": "500", "msg": error_msg, "data": []}
    
    def get_account_balance(self) -> Dict[str, Any]:
        """获取账户余额
        
        Returns:
            账户余额
        """
        return self._make_request("GET", "/api/v5/account/balance")
    
    def get_position(self, inst_id: str = None) -> Dict[str, Any]:
        """获取持仓信息
        
        Args:
            inst_id: 交易对
            
        Returns:
            持仓信息
        """
        params = {"instId": inst_id} if inst_id else {}
        return self._make_request("GET", "/api/v5/account/position", params=params)
    
    def place_order(self, inst_id: str, side: str, pos_side: str, ord_type: str, sz: str, px: str = None, 
                    tgt_ccy: str = None, cl_ord_id: str = None) -> Dict[str, Any]:
        """下单
        
        Args:
            inst_id: 交易对
            side: 买卖方向
            pos_side: 持仓方向
            ord_type: 订单类型
            sz: 下单数量
            px: 下单价格
            tgt_ccy: 交易货币
            cl_ord_id: 客户订单ID
            
        Returns:
            下单结果
        """
        data = {
            "instId": inst_id,
            "side": side,
            "posSide": pos_side,
            "ordType": ord_type,
            "sz": sz
        }
        
        if px:
            data["px"] = px
        if tgt_ccy:
            data["tgtCcy"] = tgt_ccy
        if cl_ord_id:
            data["clOrdId"] = cl_ord_id
        
        return self._make_request("POST", "/api/v5/trade/order", data=data)
    
    def cancel_order(self, inst_id: str, ord_id: str = None, cl_ord_id: str = None) -> Dict[str, Any]:
        """撤单
        
        Args:
            inst_id: 交易对
            ord_id: 订单ID
            cl_ord_id: 客户订单ID
            
        Returns:
            撤单结果
        """
        data = {"instId": inst_id}
        
        if ord_id:
            data["ordId"] = ord_id
        if cl_ord_id:
            data["clOrdId"] = cl_ord_id
        
        return self._make_request("POST", "/api/v5/trade/cancel-order", data=data)
    
    def get_order(self, inst_id: str, ord_id: str = None, cl_ord_id: str = None) -> Dict[str, Any]:
        """获取订单信息
        
        Args:
            inst_id: 交易对
            ord_id: 订单ID
            cl_ord_id: 客户订单ID
            
        Returns:
            订单信息
        """
        params = {"instId": inst_id}
        
        if ord_id:
            params["ordId"] = ord_id
        if cl_ord_id:
            params["clOrdId"] = cl_ord_id
        
        return self._make_request("GET", "/api/v5/trade/order", params=params)
    
    def get_order_list(self, inst_id: str, ord_type: str = None, state: str = None, 
                      after: str = None, before: str = None, limit: str = None) -> Dict[str, Any]:
        """获取订单列表
        
        Args:
            inst_id: 交易对
            ord_type: 订单类型
            state: 订单状态
            after: 分页游标
            before: 分页游标
            limit: 分页大小
            
        Returns:
            订单列表
        """
        params = {"instId": inst_id}
        
        if ord_type:
            params["ordType"] = ord_type
        if state:
            params["state"] = state
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit
        
        return self._make_request("GET", "/api/v5/trade/orders-pending", params=params)
    
    def get_market_data(self, inst_id: str) -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            inst_id: 交易对
            
        Returns:
            市场数据
        """
        params = {"instId": inst_id}
        return self._make_request("GET", "/api/v5/market/ticker", params=params)
    
    def get_candlesticks(self, inst_id: str, bar: str, after: str = None, before: str = None, limit: str = None) -> Dict[str, Any]:
        """获取K线数据
        
        Args:
            inst_id: 交易对
            bar: 时间周期
            after: 分页游标
            before: 分页游标
            limit: 分页大小
            
        Returns:
            K线数据
        """
        params = {
            "instId": inst_id,
            "bar": bar
        }
        
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit
        
        return self._make_request("GET", "/api/v5/market/candles", params=params)
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取API调用统计
        
        Returns:
            API调用统计
        """
        return self.api_stats
    
    def get_dns_stats(self) -> Dict[str, Any]:
        """获取DNS解析统计
        
        Returns:
            DNS解析统计
        """
        return self.dns_stats
    
    def get_network_errors(self) -> List[Dict[str, Any]]:
        """获取网络错误记录
        
        Returns:
            网络错误记录
        """
        return self.network_errors
    
    def clear_dns_cache(self):
        """清除DNS缓存"""
        self.dns_cache.clear()
        self.dns_stats["resolved_count"] = 0
        self.dns_stats["failed_count"] = 0
        self.dns_stats["last_resolved"] = None
        logger.info("DNS统计信息已重置")
    
    def clear_api_stats(self):
        """清除API调用统计"""
        self.api_stats["total_calls"] = 0
        self.api_stats["successful_calls"] = 0
        self.api_stats["failed_calls"] = 0
        self.api_stats["last_call"] = None
        logger.info("API统计信息已重置")
    
    def clear_network_errors(self):
        """清除网络错误记录"""
        self.network_errors.clear()
        logger.info("网络错误记录已重置")
