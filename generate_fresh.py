#!/usr/bin/env python3
"""生成新鲜周报 - 优化版，快速跳过失败源"""

import sys
sys.path.insert(0, '/home/gem/workspace/agent/workspace/skills/ai_cv_weekly')

import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from core.filter import ItemFilter
from core.editor import WeeklyEditor
from core.renderer_jinja2 import ReportRenderer
from core.sender import EmailSender

# 简化的数据获取 - 只使用可靠的源
async def fetch_reliable_sources():
    """获取可靠的数据源"""
    items = []
    
    # GitHub 热门项目
    print("【GitHub】获取热门项目...")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            # GitHub trending repos
            headers = {"Accept": "application/vnd.github.v3+json"}
            urls = [
                "https://api.github.com/search/repositories?q=ocr+computer+vision+created:>2025-03-09&sort=updated&order=desc&per_page=30",
                "https://api.github.com/search/repositories?q=deep+learning+image+created:>2025-03-09&sort=updated&order=desc&per_page=20",
            ]
            for url in urls:
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for repo in data.get('items', []):
                                items.append({
                                    'title': repo.get('name', ''),
                                    'description': repo.get('description', ''),
                                    'url': repo.get('html_url', ''),
                                    'source': 'github',
                                    'published': repo.get('updated_at', ''),
                                    'stars': repo.get('stargazers_count', 0),
                                    'domain_tags': ['CV', 'OCR'] if 'ocr' in repo.get('name', '').lower() else ['AI']
                                })
                except Exception as e:
                    print(f"   ⚠️ GitHub API 错误: {e}")
                    continue
        print(f"   ✅ GitHub: {len(items)} 条")
    except Exception as e:
        print(f"   ⚠️ GitHub 失败: {e}")
    
    # arXiv 论文
    print("【arXiv】获取最新论文...")
    try:
        import urllib.request
        import xml.etree.ElementTree as ET
        
        arxiv_url = "http://export.arxiv.org/api/query?search_query=cat:cs.CV+OR+cat:cs.LG&start=0&max_results=30&sortBy=submittedDate&sortOrder=descending"
        
        with urllib.request.urlopen(urllib.request.Request(arxiv_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15) as response:
            data = response.read().decode('utf-8')
            root = ET.fromstring(data)
            
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('.//atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:link[@type="text/html"]', ns)
                published = entry.find('atom:published', ns)
                
                if title is not None:
                    items.append({
                        'title': title.text.strip().replace('\n', ' '),
                        'description': summary.text.strip()[:500] if summary is not None else '',
                        'url': link.get('href') if link is not None else '',
                        'source': 'arxiv',
                        'published': published.text if published is not None else '',
                        'domain_tags': ['CV', 'Paper']
                    })
        print(f"   ✅ arXiv: {len(items)} 条")
    except Exception as e:
        print(f"   ⚠️ arXiv 失败: {e}")
    
    # Hacker News
    print("【Hacker News】获取热门...")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            # Get top stories
            async with session.get("https://hacker-news.firebaseio.com/v0/topstories.json") as resp:
                if resp.status == 200:
                    story_ids = await resp.json()
                    story_ids = story_ids[:15]
                    
                    for story_id in story_ids:
                        try:
                            async with session.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json") as story_resp:
                                if story_resp.status == 200:
                                    story = await story_resp.json()
                                    title = story.get('title', '')
                                    if any(kw in title.lower() for kw in ['ai', 'ml', 'vision', 'ocr', 'image', 'neural', 'deep learning', 'model']):
                                        items.append({
                                            'title': title,
                                            'description': '',
                                            'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                            'source': 'hackernews',
                                            'published': datetime.fromtimestamp(story.get('time', 0)).isoformat(),
                                            'domain_tags': ['AI', 'News']
                                        })
                        except:
                            continue
        print(f"   ✅ Hacker News: {len(items)} 条")
    except Exception as e:
        print(f"   ⚠️ Hacker News 失败: {e}")
    
    return items

async def main():
    print("="*60)
    print("🦞 AI/CV Weekly - 新鲜生成版")
    print("="*60)
    print()
    
    now = datetime.now()
    time_range_days = 7
    time_range = f"{(now - timedelta(days=time_range_days)).strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
    
    print(f"时间范围：{time_range}")
    print(f"当前日期：{now.strftime('%Y-%m-%d')}")
    print()
    
    # 数据提取
    print("【Layer 1】数据提取层...")
    items = await fetch_reliable_sources()
    
    print(f"\n   总计抓取：{len(items)} 条")
    
    if len(items) < 5:
        print("❌ 数据不足，无法生成周报")
        return False
    
    # 过滤
    print("\n【过滤层】CV/OCR 优先...")
    item_filter = ItemFilter()
    selected = item_filter.filter_and_rank(items, max_keep=25)
    
    cv_count = sum(1 for i in selected if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR', 'Medical Imaging']))
    print(f"   精选 {len(selected)} 条")
    print(f"   CV/OCR 相关：{cv_count}/{len(selected)} 条")
    
    if len(selected) < 3:
        print("❌ 过滤后内容不足")
        return False
    
    # 主编整合
    print("\n【Layer 2】主编整合层...")
    editor = WeeklyEditor()
    issue_number = 36  # 新期号
    
    result = editor.generate(selected, issue_number, max_retries=2)
    
    if not result.get('success'):
        print(f"❌ 生成失败：{result.get('error')}")
        return False
    
    markdown = result.get('markdown', '')
    quality_score = result.get('quality_score', 0)
    print(f"   ✅ 周报已生成（{len(markdown)} 字符）")
    print(f"   质量评分：{quality_score:.0%}")
    
    # 渲染
    print("\n【Layer 3】数据渲染层...")
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    renderer = ReportRenderer(output_dir)
    render_result = renderer.render(
        markdown, 
        issue_number, 
        time_range,
        stats={
            "total_items": len(items),
            "cv_count": cv_count,
            "source_count": 3
        }
    )
    
    html_path = render_result.get('html_path', '')
    md_path = render_result.get('md_path', '')
    print(f"   ✅ HTML: {html_path}")
    print(f"   ✅ Markdown: {md_path}")
    
    # 发送邮件
    print("\n【邮件发送】...")
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
    print()
    print(f"📊 统计:")
    print(f"   期号：第 {issue_number} 期")
    print(f"   时间：{time_range}")
    print(f"   原始数据：{len(items)} 条")
    print(f"   精选：{len(selected)} 条")
    print(f"   CV/OCR：{cv_count} 条")
    print(f"   字数：{len(markdown)}")
    print(f"   质量：{quality_score:.0%}")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)