# 🦞 LunaClaw Brief — OpenClaw Skill

**Pluggable AI-Powered Report Engine** | 插件化 AI 智能简报引擎

## Overview / 概述

LunaClaw Brief is an OpenClaw Skill that generates intelligent weekly/daily reports across multiple domains (AI/CV tech, finance/investment). It features a plugin architecture with 8-stage pipeline, multi-dimensional scoring, historical deduplication, and beautiful HTML/PDF output.

LunaClaw Brief 是一个 OpenClaw Skill，可生成多领域（AI/CV 技术、金融投资）的智能周报/日报。采用插件化架构，8 阶段管线，多维打分，历史去重，精美 HTML/PDF 输出。

## Capabilities / 核心能力

- **4 built-in presets**: AI/CV Weekly, AI Daily, Finance Weekly, Finance Daily
- **6 data sources**: GitHub (with competitor discovery), arXiv, Hacker News, Papers with Code, Financial News (RSS)
- **Smart scoring**: Domain keywords + source weights + community signals (stars, points, comments)
- **Historical dedup**: Content fingerprinting with configurable time window
- **LLM editor**: Sharp opinionated reviews (🦞 Claw Critique), project comparisons
- **Quality control**: Auto-check structure/word count/sections, retry if below threshold
- **Beautiful output**: Dark-theme HTML with Luna logo, optional PDF, email delivery

## Usage / 使用方式

### Via CLI

```bash
python run.py                              # AI/CV Weekly (default)
python run.py --preset ai_daily            # AI Daily Brief
python run.py --preset finance_weekly      # Finance Weekly
python run.py --preset finance_daily       # Finance Daily
python run.py --preset ai_cv_weekly --email  # Generate + send email
python run.py --hint "focus on OCR"        # Custom hint
```

### Via OpenClaw Skill API

```python
from run import generate_report

result = generate_report({
    "preset": "finance_weekly",
    "hint": "重点关注半导体和 AI 芯片",
    "send_email": True,
})
# result: { "success": True, "html_path": "...", "pdf_path": "...", ... }
```

### Trigger Phrases / 触发短语

- "生成周报" / "generate weekly report"
- "生成金融周报" / "generate finance report"
- "生成日报" / "generate daily brief"
- "AI CV 周报" / "金融日报"

## Architecture / 架构亮点

| Pattern | Where |
|---------|-------|
| Adapter | `BaseSource` → 5 source adapters |
| Strategy | `BaseEditor` → 4 editor strategies |
| Pipeline | 8-stage `ReportPipeline` |
| Registry | `@register_source` / `@register_editor` decorators |
| Observer | `MiddlewareChain` for timing, metrics, custom hooks |
| Factory | `create_sources()` / `create_editor()` |
| Cache | `FileCache` with TTL for API responses |

## Extending / 扩展

Implement `BaseSource` + `@register_source("name")` to add a data source.
Implement `BaseEditor` + `@register_editor("name")` to add an editor strategy.
Add a `PresetConfig` to `brief/presets.py` to create a new report type.
Create a Jinja2 template in `templates/` for custom layouts.

## Configuration / 配置

Global config in `config.yaml`. Secrets in `config.local.yaml` (gitignored).

```yaml
# config.local.yaml
llm:
  api_key: "your-key"
```

## Output / 输出

- **HTML**: Self-contained with embedded Luna logo, dark theme
- **Markdown**: Raw LLM output for further processing
- **PDF**: Via WeasyPrint (optional dependency)
- **Email**: HTML body + PDF attachment

---

*Built by llx & Luna 🐱 — where the claw meets the code.* 🦞
