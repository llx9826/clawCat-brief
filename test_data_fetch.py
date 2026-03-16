#!/usr/bin/env python3
"""测试数据抓取 - 诊断卡住问题"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import config
from logger import setup_logger
from core.fetcher import DataFetcher

setup_logger(level='INFO')

async def test_fetch():
    print("="*60)
    print("测试数据抓取（超时 30 秒）")
    print("="*60)
    
    proxy = config.get_proxy()
    github_token = config.get_github_token()
    
    print(f"代理: {proxy or '无'}")
    print(f"GitHub Token: {'已配置' if github_token else '未配置'}")
    print()
    
    try:
        async with DataFetcher(
            timeout=10,  # 缩短超时
            proxy=proxy,
            github_token=github_token
        ) as fetcher:
            print("开始抓取...")
            
            # 使用 asyncio.wait_for 设置总超时
            result = await asyncio.wait_for(
                fetcher.fetch_all({"time_range_days": 7}),
                timeout=30
            )
            
            print()
            print("="*60)
            print("抓取完成!")
            print("="*60)
            print(f"总条目: {result.get('total_count', 0)}")
            print(f"成功源: {', '.join(result.get('sources_used', []))}")
            print(f"失败源: {', '.join(result.get('failed_sources', []))}")
            
    except asyncio.TimeoutError:
        print("\n❌ 抓取超时（30秒）")
    except Exception as e:
        print(f"\n❌ 抓取异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fetch())
