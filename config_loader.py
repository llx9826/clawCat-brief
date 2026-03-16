#!/usr/bin/env python3
"""
AI/CV Weekly - 配置加载器
支持 YAML 配置 + 环境变量覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理类"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_paths = [
            Path(__file__).parent / "config.local.yaml",  # 本地配置（优先）
            Path(__file__).parent / "config.yaml",        # 默认配置
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 解析环境变量
                    config = self._resolve_env_vars(config)
                    return config
        
        # 如果没有配置文件，返回默认配置
        return self._default_config()
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """解析环境变量占位符 ${VAR_NAME}"""
        if isinstance(obj, str):
            if obj.startswith('${') and obj.endswith('}'):
                var_name = obj[2:-1]
                return os.getenv(var_name, '')
            return obj
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        return obj
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "llm": {
                "provider": "bailian",
                "api_key": os.getenv("BAILIAN_API_KEY", ""),
                "base_url": "https://coding.dashscope.aliyuncs.com/v1",
                "model": "kimi-k2.5",
                "timeout": 180,
                "max_retries": 2,
                "temperature": 0.7,
            },
            "proxy": {
                "enabled": False,
                "http": None,
                "https": None,
            },
            "github": {
                "token": os.getenv("GITHUB_TOKEN", ""),
            },
            "sources": {
                "enabled": ["jiqizhixin", "36kr", "github", "arxiv", "hackernews", "paperswithcode"],
            },
            "email": {
                "smtp_server": "smtp.163.com",
                "smtp_port": 465,
                "use_ssl": True,
                "sender_email": os.getenv("EMAIL_SENDER", ""),
                "sender_password": os.getenv("EMAIL_PASSWORD", ""),
                "receiver_email": os.getenv("EMAIL_RECEIVER", ""),
            },
            "weekly": {
                "max_items": 35,
                "time_range_days": 7,
                "min_cv_ratio": 0.5,
            },
            "logging": {
                "level": "INFO",
                "file": "logs/weekly.log",
                "max_bytes": 10485760,
                "backup_count": 5,
            },
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径，如 'llm.api_key'）"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return self._config.get('llm', {})
    
    def get_proxy(self) -> str:
        """获取代理地址"""
        proxy_cfg = self._config.get('proxy', {})
        if proxy_cfg.get('enabled') and proxy_cfg.get('http'):
            return proxy_cfg.get('http')
        return None
    
    def get_github_token(self) -> str:
        """获取 GitHub Token"""
        return self._config.get('github', {}).get('token', '')
    
    def get_email_config(self) -> Dict[str, Any]:
        """获取邮件配置"""
        return self._config.get('email', {})
    
    def get_enabled_sources(self) -> list:
        """获取启用的数据源"""
        return self._config.get('sources', {}).get('enabled', [])


# 全局配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置加载
    print("当前配置：")
    print(f"LLM Model: {config.get('llm.model')}")
    print(f"Proxy: {config.get_proxy()}")
    print(f"Enabled sources: {config.get_enabled_sources()}")
