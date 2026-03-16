#!/usr/bin/env python3
"""发送最新周报"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.renderer_email import EmailReportRenderer
from core.sender import EmailSender

# 读取昨天生成的完整周报
with open('/home/gem/workspace/agent/workspace/skills/ai_cv_weekly/output/weekly_20260312_161940.md', 'r', encoding='utf-8') as f:
    markdown = f.read()

print(f"📄 加载周报内容: {len(markdown)} 字符")

# 使用新的邮件渲染器
renderer = EmailReportRenderer()
html = renderer.render(
    markdown=markdown,
    issue_number=32,
    time_range="2026-03-05 ~ 2026-03-12",
    stats={"total_items": 67, "cv_count": 27, "source_count": 12}
)

print(f"✅ 渲染完成: {len(html)} 字符")

# 发送邮件
sender = EmailSender()
success = sender.send(
    subject="🦞 AI/CV Weekly - 第32期 [正式版]",
    html_content=html,
    text_content=markdown[:1000] + "..."
)

if success:
    print("✅ 邮件发送成功!")
else:
    print("❌ 邮件发送失败")
