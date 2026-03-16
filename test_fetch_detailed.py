#!/usr/bin/env python3
"""详细测试数据抓取 - 诊断哪个源卡住"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import config
from logger import setup_logger
from core.fetcher import DataFetcher

setup_logger(level='INFO')

async def test_single_fetch(fetcher, name, func):
    """测试单个数据源"""
    print(f"  开始: {name}...", end='', flush=True)
    start = asyncio.get_event_loop().time()
    try:
        result = await asyncio.wait_for(func(), timeout=15)
        elapsed = asyncio.get_event_loop().time() - start
        print(f" ✅ {len(result)} 条 ({elapsed:.1f}s)")
        return name, result, None
    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start
        print(f" ⏱️ 超时 ({elapsed:.1f}s)")
        return name, [], "timeout"
    except Exception as e:
        elapsed = asyncio.get_event_loop().time() - start
        print(f" ❌ {str(e)[:30]} ({elapsed:.1f}s)")
        return name, [], str(e)[:50]

async def test_fetch():
    print("="*60)
    print("详细测试数据抓取")
    print("="*60)
    
    proxy = config.get_proxy()
    github_token = config.get_github_token()
    
    print(f"代理: {proxy or '无'}")
    print(f"GitHub Token: {'已配置' if github_token else '未配置'}")
    print()
    
    async with DataFetcher(
        timeout=10,
        proxy=proxy,
        github_token=github_token
    ) as fetcher:
        # 测试每个数据源
        sources = [
            ("GitHub", fetcher._fetch_github),
            ("arXiv", fetcher._fetch_arxiv),
            ("Hacker News", fetcher._fetch_hackernews),
            ("Hugging Face", fetcher._fetch_huggingface),
        ]
        
        print("逐个测试数据源:")
        for name, func in sources:
            await test_single_fetch(fetcher, name, func)
        
        print()
        print("="*60)
        print("测试完成")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_fetch())
