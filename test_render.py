#!/usr/bin/env python3
"""测试 Jinja2 渲染器"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.renderer_jinja2 import ReportRenderer
from core.sender import EmailSender

# 测试 Markdown 内容
test_markdown = """## 核心结论

- 本周 CV/OCR 领域有 3 个重要突破
- 多模态模型持续升温
- 开源社区活跃度提升

## 重点事件

### 1. PaddleOCR 发布 v2.8 版本
PaddleOCR 团队发布了 v2.8 版本，新增了对更多语种的支持，并优化了移动端推理性能。

**🦞 Claw 锐评**：版本更新频率不错，但文档还是老问题——示例代码和实际 API 对不上，新手容易踩坑。

### 2. Meta 发布 SAM 2.0
Segment Anything Model 2.0 发布，支持视频分割，效果惊艳。

**🦞 Claw 锐评**：学术界又要跟进了，但落地成本太高，中小企业玩不起。

## 开源项目

### 1. EasyOCR
- GitHub: [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- ⭐ 20k+ stars
- 支持 80+ 语种，开箱即用

**🦞 Claw 锐评**：易用性确实好，但性能不如 PaddleOCR，适合快速原型，不适合生产环境。

## 论文推荐

### 1. OCR-Free Document Understanding
arXiv 上的新论文，提出了一种无需 OCR 的文档理解方法。

**🦞 Claw 锐评**：思路很新颖，但实验数据集太小，说服力不够，需要更大规模的验证。

## 趋势分析

- **端到端文档理解**：OCR + NLP 的 pipeline 正在被淘汰
- **多模态融合**：视觉-语言模型成为主流
- **边缘部署**：移动端 OCR 需求激增

## Claw 复盘

本周整体信息量不错，CV/OCR 占比达标。但开源项目同质化严重，真正有创新的不多。建议下周关注文档理解领域的新进展，特别是端到端方法的突破。

**🦞 Claw 锐评**：周报生成流程已经稳定，但数据源质量还有提升空间，特别是中文技术媒体的抓取成功率需要优化。
"""

# 渲染
print("="*60)
print("🦞 测试 Jinja2 渲染器")
print("="*60)

renderer = ReportRenderer()
result = renderer.render(
    markdown=test_markdown,
    issue_number=999,
    time_range="2026-03-06 ~ 2026-03-13",
    stats={"total_items": 156, "cv_count": 89, "source_count": 12}
)

print(f"\n✅ 渲染完成!")
print(f"   HTML: {result['html_path']}")
print(f"   Markdown: {result['md_path']}")

# 发送邮件
print("\n" + "="*60)
print("📧 发送测试邮件")
print("="*60)

with open(result['html_path'], 'r', encoding='utf-8') as f:
    html_content = f.read()

sender = EmailSender()
success = sender.send(
    subject="🦞 AI/CV Weekly - 第999期 [Jinja2模板测试]",
    html_content=html_content,
    text_content=test_markdown[:500] + "..."
)

if success:
    print("\n✅ 邮件发送成功!")
else:
    print("\n❌ 邮件发送失败")
