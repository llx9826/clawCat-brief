#!/usr/bin/env python3
"""快速生成周报 - 使用简化流程"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from datetime import datetime, timedelta
from core.fetcher import DataFetcher
from core.filter import ItemFilter
from core.editor import WeeklyEditor
from core.renderer_jinja2 import ReportRenderer
from core.sender import EmailSender

async def quick_generate():
    """快速生成周报"""
    print("="*60)
    print("🦞 AI/CV Weekly - 快速生成版")
    print("="*60)
    print()
    
    now = datetime.now()
    time_range_days = 7
    time_range = f"{(now - timedelta(days=time_range_days)).strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
    
    print(f"时间范围：{time_range}")
    print()
    
    # 数据提取
    print("【数据提取】...")
    async with DataFetcher(timeout=30) as fetcher:
        fetch_result = await fetcher.fetch_all({
            "time_range_days": time_range_days
        })
    
    items = fetch_result.get('items', [])
    sources_used = fetch_result.get('sources_used', [])
    
    print(f"   抓取到 {len(items)} 条")
    print(f"   成功源：{len(sources_used)} 个")
    
    if len(items) < 3:
        print("❌ 数据不足")
        return False
    
    # 过滤
    print("\n【过滤层】CV/OCR 优先...")
    item_filter = ItemFilter()
    selected = item_filter.filter_and_rank(items, max_keep=35)
    
    cv_count = sum(1 for i in selected if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR', 'Medical Imaging']))
    print(f"   精选 {len(selected)} 条")
    print(f"   CV/OCR 相关：{cv_count}/{len(selected)} 条")
    
    if len(selected) < 3:
        print("❌ 过滤后内容不足")
        return False
    
    # 主编整合
    print("\n【主编整合】...")
    editor = WeeklyEditor()
    issue_number = 33  # 当前期号
    
    result = editor.generate(selected, issue_number, max_retries=2)
    
    if not result.get('success'):
        print(f"❌ 生成失败：{result.get('error')}")
        return False
    
    markdown = result.get('markdown', '')
    quality_score = result.get('quality_score', 0)
    print(f"   ✅ 周报已生成（{len(markdown)} 字符）")
    print(f"   质量评分：{quality_score:.0%}")
    
    # 渲染
    print("\n【渲染】...")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    renderer = ReportRenderer(output_dir)
    render_result = renderer.render(
        markdown, 
        issue_number, 
        time_range,
        stats={
            "total_items": len(items),
            "cv_count": cv_count,
            "source_count": len(sources_used)
        }
    )
    
    html_path = render_result.get('html_path', '')
    md_path = render_result.get('md_path', '')
    print(f"   ✅ HTML: {html_path}")
    print(f"   ✅ Markdown: {md_path}")
    
    # 发送邮件
    print("\n【发送邮件】...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    sender = EmailSender()
    subject = f"🦞 AI/CV Weekly - 第{issue_number}期 ({time_range})"
    success = sender.send(subject, html_content, markdown[:1000] + "...")
    
    if success:
        print("   ✅ 邮件已发送!")
    else:
        print("   ⚠️ 邮件发送失败")
    
    print()
    print("="*60)
    print("✅ 完成!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    result = asyncio.run(quick_generate())
    sys.exit(0 if result else 1)
