#!/usr/bin/env python3
"""OCR 小报生成器"""

import sys
sys.path.insert(0, '/home/gem/workspace/agent/workspace/skills/ai_cv_weekly')

import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from core.renderer_jinja2 import ReportRenderer
from weasyprint import HTML
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders
import json
import urllib.request
import xml.etree.ElementTree as ET

async def fetch_ocr_data():
    items = []
    
    print("【GitHub OCR】...")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        headers = {"Accept": "application/vnd.github.v3+json"}
        queries = [
            "ocr+text+recognition+created:>2025-03-09",
            "ocr+document+scanner+created:>2025-03-09",
            "paddleocr+tesseract+created:>2025-03-09",
        ]
        for q in queries:
            try:
                url = f"https://api.github.com/search/repositories?q={q}&sort=updated&order=desc&per_page=10"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get('items', []):
                            items.append({
                                'title': repo.get('name', ''),
                                'description': repo.get('description', '') or '',
                                'url': repo.get('html_url', ''),
                                'source': 'github',
                                'published': repo.get('updated_at', ''),
                                'stars': repo.get('stargazers_count', 0),
                                'domain_tags': ['OCR'],
                                'raw_text': f"{repo.get('description', '') or ''} Stars: {repo.get('stargazers_count', 0)}"
                            })
            except:
                continue
    
    github_count = len(items)
    print(f"   ✅ GitHub OCR: {github_count} 条")
    
    print("【arXiv OCR】...")
    try:
        url = "http://export.arxiv.org/api/query?search_query=all:ocr+OR+all:text+recognition&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read().decode('utf-8')
            root = ET.fromstring(data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('.//atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:link[@type="text/html"]', ns)
                published = entry.find('atom:published', ns)
                if title is not None:
                    title_text = title.text.strip().replace('\n', ' ')
                    if any(k in title_text.lower() for k in ['ocr', 'text recognition', 'document']):
                        items.append({
                            'title': title_text[:120],
                            'description': summary.text.strip()[:400] if summary is not None else '',
                            'url': link.get('href') if link is not None else '',
                            'source': 'arxiv',
                            'published': published.text if published is not None else '',
                            'domain_tags': ['OCR', 'Paper'],
                            'raw_text': summary.text.strip()[:500] if summary is not None else ''
                        })
    except Exception as e:
        print(f"   ⚠️ {e}")
    
    print(f"   ✅ arXiv OCR: {len(items) - github_count} 条")
    
    return items

async def main():
    print("="*60)
    print("📰 OCR 小报 - 专注 OCR 领域")
    print("="*60)
    
    now = datetime.now()
    time_range = f"{(now - timedelta(days=7)).strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
    print(f"\n时间范围：{time_range}")
    
    items = await fetch_ocr_data()
    print(f"\n📊 总计：{len(items)} 条 OCR 内容")
    
    if len(items) < 5:
        print("❌ OCR 数据不足")
        return False
    
    print("\n【生成 OCR 小报】...")
    
    from llm_client import LLMClient
    llm = LLMClient()
    
    system_prompt = """你是 OCR 领域的技术专家，专注于光学字符识别、文档理解、场景文字识别。

【周报结构 - 6章节】
## 一、本周 OCR 核心结论
## 二、OCR 开源项目动态
## 三、OCR 论文速递
## 四、OCR 技术趋势分析
## 五、OCR 商业观察
## 六、🦞 Claw OCR 锐评

【要求】
1. 所有内容必须聚焦 OCR 领域
2. 深入分析 OCR 技术趋势
3. 每个项目/论文包含：是什么、解决什么问题、技术特点、🦞 Claw 锐评
4. 总字数 4000-6000 字
5. 必须生成全部 6 个章节"""

    user_prompt = f"""请生成第 1 期 OCR 小报。

时间范围: {time_range}
内容: {len(items)} 条 OCR 相关内容

"""
    
    for i, item in enumerate(items[:20], 1):
        tags = ', '.join(item.get('domain_tags', []))
        user_prompt += f"""{i}. **{item['title']}**
   来源：{item['source']} | {tags}
   {item['raw_text'][:250]}

"""
    
    user_prompt += "请生成 OCR 小报（全部6章节）："
    
    try:
        response = llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=8000
        )
        
        if not response:
            print("❌ LLM 返回为空")
            return False
        
        markdown = response.strip()
        if markdown.startswith('```markdown'):
            markdown = markdown[11:]
        if markdown.startswith('```'):
            markdown = markdown[3:]
        if markdown.endswith('```'):
            markdown = markdown[:-3]
        markdown = markdown.strip()
        
        # 添加标题
        markdown = f"# 📰 OCR 小报 第 1 期\n\n**时间范围**：{time_range}  \n**主编**：Claw\n\n---\n\n" + markdown
        
        print(f"✅ 已生成 ({len(markdown)} 字符)")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False
    
    sections = [line for line in markdown.split('\n') if line.startswith('## ')]
    print(f"\n📋 章节 ({len(sections)}/6):")
    for s in sections:
        print(f"   {s}")
    
    print("\n【渲染 HTML】...")
    output_dir = Path('output')
    renderer = ReportRenderer(output_dir)
    render_result = renderer.render(markdown, 1, time_range,
        stats={"total_items": len(items), "cv_count": len(items), "source_count": 2})
    
    html_path = render_result.get('html_path', '')
    print(f"✅ {html_path}")
    
    print("\n【生成 PDF】...")
    pdf_path = html_path.replace('.html', '.pdf')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"✅ PDF: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF 失败: {e}")
        pdf_path = None
    
    print("\n【发送邮件】...")
    with open('/home/gem/workspace/agent/workspace/email_config.json', 'r') as f:
        config = json.load(f)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(f'📰 OCR 小报 - 第1期 ({time_range})', 'utf-8')
    msg['From'] = f"OCR 小报 <{config['sender_email']}>"
    msg['To'] = config['receiver_email']
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    if pdf_path:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        pdf_attachment = MIMEBase('application', 'octet-stream')
        pdf_attachment.set_payload(pdf_data)
        encoders.encode_base64(pdf_attachment)
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename='OCR_小报_第1期.pdf')
        msg.attach(pdf_attachment)
        print("✅ PDF 附件已添加")
    
    try:
        server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        server.login(config['sender_email'], config['sender_password'])
        server.sendmail(config['sender_email'], [config['receiver_email']], msg.as_string())
        server.quit()
        print("✅ 邮件已发送!")
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())