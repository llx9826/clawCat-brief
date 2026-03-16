#!/usr/bin/env python3
"""
AI/CV Weekly - LLM 客户端
使用百炼 API (通义千问)
"""

import os
import sys
import requests
from typing import Dict, Any, List
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import config


class LLMClient:
    """百炼 LLM 客户端（同步版本）"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        # 优先使用传入参数，其次配置文件，最后环境变量
        llm_cfg = config.get_llm_config()
        
        self.api_key = api_key or llm_cfg.get('api_key') or os.getenv("BAILIAN_API_KEY", "")
        self.base_url = base_url or llm_cfg.get('base_url') or os.getenv("BAILIAN_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1")
        self.model = model or llm_cfg.get('model') or os.getenv("BAILIAN_MODEL", "kimi-k2.5")
        self.timeout = llm_cfg.get('timeout', 180)
        
        if not self.api_key:
            raise ValueError("API Key 未设置。请设置 BAILIAN_API_KEY 环境变量或在在 config.local.yaml 中指定。")
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, 
             max_tokens: int = 4096) -> str:
        """发送聊天请求（同步）"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"API 错误：{resp.status_code} - {resp.text[:200]}")
                return ""
        except Exception as e:
            print(f"LLM 请求失败：{type(e).__name__}: {e}")
            return ""


if __name__ == "__main__":
    # 测试
    try:
        client = LLMClient()
        response = client.chat([{"role": "user", "content": "Hello"}], max_tokens=10)
        print(f"测试成功: {response}")
    except ValueError as e:
        print(f"配置错误: {e}")
