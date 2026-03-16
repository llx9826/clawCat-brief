#!/usr/bin/env python3
"""调试渲染器"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.renderer_jinja2 import ReportRenderer

# 测试 Markdown 内容
test_markdown = """## 核心结论

- 本周 CV/OCR 领域有 3 个重要突破
- 多模态模型持续升温
- 开源社区活跃度提升

## 重点事件

### 1. PaddleOCR 发布 v2.8 版本
PaddleOCR 团队发布了 v2.8 版本，新增了对更多语种的支持，并优化了移动端推理性能。

**🦞 Claw 锐评**：版本更新频率不错，但文档还是老问题——示例代码和实际 API 对不上，新手容易踩坑。
"""

renderer = ReportRenderer()
sections = renderer._parse_sections(test_markdown)

print("解析到的章节数:", len(sections))
for i, section in enumerate(sections):
    print(f"\n=== 章节 {i+1}: {section['title']} ===")
    print(f"内容长度: {len(section['content'])} 字符")
    print(f"内容预览: {section['content'][:200]}...")
