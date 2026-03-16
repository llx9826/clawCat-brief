#!/usr/bin/env python3
"""测试数据抓取"""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import config
from core.fetcher import DataFetcher

async def test_fetch():
    print("="*60)
    print("🦞 测试数据抓取（优化后）")
    print("="*60)
    
    import time
    start = time.time()
    
    # 使用 async with 自动管理 session
    async with DataFetcher(
        timeout=30,
        proxy=config.get_proxy(),
        github_token=config.get_github_token()
    ) as fetcher:
        # 只测试 Karpathy RSS
        print("\n【测试 Karpathy RSS 抓取】")
        items = await fetcher._fetch_karpathy_rss()
    
    elapsed = time.time() - start
    print(f"\n✅ 测试完成！")
    print(f"   耗时: {elapsed:.1f} 秒")
    print(f"   获取条目: {len(items)} 条")

if __name__ == "__main__":
    asyncio.run(test_fetch())
