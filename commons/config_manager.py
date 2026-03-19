import json
import os
from typing import Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.config = {}
        else:
            logger.warning(f"配置文件不存在: {self.config_file}")
            self.config = {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        # 支持嵌套键，例如 "api.key"
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        # 支持嵌套键，例如 "api.key"
        keys = key.split(".")
        config = self.config
        
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                config[k] = value
            else:
                if k not in config or not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
        
        logger.info(f"配置设置: {key} = {value}")
    
    def delete(self, key: str):
        """删除配置
        
        Args:
            key: 配置键
        """
        # 支持嵌套键，例如 "api.key"
        keys = key.split(".")
        config = self.config
        
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                if k in config:
                    del config[k]
                    logger.info(f"配置删除: {key}")
            else:
                if k not in config or not isinstance(config[k], dict):
                    break
                config = config[k]
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            所有配置
        """
        return self.config
    
    def update(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        logger.info("配置更新成功")
    
    def clear(self):
        """清空配置"""
        self.config = {}
        logger.info("配置已清空")
    
    def has(self, key: str) -> bool:
        """检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            是否存在
        """
        # 支持嵌套键，例如 "api.key"
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        
        return True
