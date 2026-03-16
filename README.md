# 🦞 LunaClaw Brief

**Pluggable AI-Powered Report Engine** | 插件化 AI 智能简报引擎

> Built with ❤️ by **llx** & **Luna** 🐱 (a brown tabby Maine Coon)

---

## What is LunaClaw Brief?

LunaClaw Brief is an extensible report generation engine that fetches content from multiple sources, scores and selects the most relevant items, generates opinionated reports via LLM, and renders them into beautiful HTML/PDF with email delivery.

LunaClaw Brief 是一个可扩展的报告生成引擎，从多个数据源抓取内容，通过多维打分选材，由 LLM 生成有观点的深度报告，渲染为精美的 HTML/PDF 并支持邮件推送。

## Architecture / 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ReportPipeline                            │
│  ┌───────┐  ┌───────┐  ┌────────┐  ┌───────┐  ┌─────────┐ │
│  │ Fetch │→│ Score │→│ Select │→│ Dedup │→│  Edit   │ │
│  │(async)│  │(multi)│  │(Top-K) │  │(hist) │  │  (LLM)  │ │
│  └───────┘  └───────┘  └────────┘  └───────┘  └─────────┘ │
│       ↓                                             ↓       │
│  ┌─────────┐                              ┌─────────────┐  │
│  │ Quality │←────────────────────────────│   Render    │  │
│  │  Check  │                              │(Jinja2+PDF) │  │
│  └─────────┘                              └─────────────┘  │
│       ↓                                             ↓       │
│  ┌─────────┐                              ┌─────────────┐  │
│  │  Retry  │                              │   Email     │  │
│  │ (if<70%)│                              │ (HTML+PDF)  │  │
│  └─────────┘                              └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  MiddlewareChain: Timing · Metrics · Custom Hooks           │
│  BriefLogger: Structured logging with phase context          │
└─────────────────────────────────────────────────────────────┘
```

## Design Patterns / 设计模式

| Pattern | Application | 应用 |
|---------|-------------|------|
| **Adapter** | `BaseSource` → GitHub / arXiv / HN / PwC / FinNews | 数据源统一接口 |
| **Strategy** | `BaseEditor` → WeeklyEditor / DailyEditor / FinanceEditor | 不同 LLM prompt 策略 |
| **Pipeline** | `ReportPipeline` — 8-stage flow | 8 阶段管线 |
| **Registry** | `@register_source` / `@register_editor` decorators | 装饰器零配置注册 |
| **Observer** | `MiddlewareChain` + `PipelineMiddleware` | 管线钩子系统 |
| **Factory** | `create_sources()` / `create_editor()` | 工厂函数动态创建 |
| **Dataclass** | `Item` / `ScoredItem` / `PresetConfig` / `ReportDraft` | 强类型数据模型 |
| **Cache** | `FileCache` with TTL | 文件级 TTL 缓存 |

## Presets / 预设

| Preset | Description | Sources |
|--------|-------------|---------|
| `ai_cv_weekly` | AI/CV tech deep-dive weekly | GitHub, arXiv, HN, PwC |
| `ai_daily` | AI tech daily brief | GitHub, arXiv, HN |
| `finance_weekly` | Investment-oriented market weekly | FinNews, HN |
| `finance_daily` | Market flash daily | FinNews, HN |

## Quick Start / 快速开始

```bash
# Install dependencies
pip install -r requirements.txt

# Configure LLM key (create config.local.yaml, gitignored)
cat > config.local.yaml << 'EOF'
llm:
  api_key: "your-api-key-here"
EOF

# Generate AI/CV Weekly (default)
python run.py

# Generate AI Daily Brief
python run.py --preset ai_daily

# Generate Finance Weekly
python run.py --preset finance_weekly

# Generate and send via email
python run.py --preset ai_cv_weekly --email

# Custom hint for LLM
python run.py --hint "focus on OCR and document AI"
```

## Project Structure / 项目结构

```
lunaclaw-brief/
├── brief/                          # Core engine / 核心引擎
│   ├── models.py                   # Data models (Item, ScoredItem, PresetConfig...)
│   ├── presets.py                  # Preset definitions (4 presets)
│   ├── pipeline.py                 # 8-stage ReportPipeline + Middleware
│   ├── registry.py                 # Plugin Registry (@register_source/editor)
│   ├── middleware.py               # Pipeline hooks (Timing, Metrics, Custom)
│   ├── log.py                      # Structured logging with context binding
│   ├── cache.py                    # File-based TTL cache
│   ├── scoring.py                  # Multi-dimensional Scorer + Selector
│   ├── dedup.py                    # Historical dedup (UsedItemStore) + IssueCounter
│   ├── quality.py                  # LLM output QualityChecker
│   ├── llm.py                      # OpenAI-compatible LLM client
│   ├── sender.py                   # Email sender (HTML + PDF attachment)
│   ├── sources/                    # Data source adapters
│   │   ├── base.py                 #   BaseSource (abstract)
│   │   ├── github.py               #   GitHub (with competitor discovery)
│   │   ├── arxiv.py                #   arXiv papers
│   │   ├── hackernews.py           #   Hacker News
│   │   ├── paperswithcode.py       #   Papers with Code
│   │   └── finnews.py              #   Financial news (HN + RSS)
│   ├── editors/                    # LLM editor strategies
│   │   ├── base.py                 #   BaseEditor (retry + backoff)
│   │   ├── weekly.py               #   Tech weekly (with project comparison)
│   │   ├── daily.py                #   Tech daily
│   │   └── finance.py              #   Finance weekly + daily
│   └── renderer/                   # Rendering layer
│       ├── markdown_parser.py      #   Markdown → structured sections
│       └── jinja2.py               #   Jinja2 + WeasyPrint PDF
├── templates/                      # Jinja2 templates
│   ├── base.html                   #   Base layout (with Luna logo)
│   ├── weekly.html                 #   Tech weekly template
│   ├── daily.html                  #   Daily template
│   └── finance.html                #   Finance template (with disclaimer)
├── static/                         # Static assets
│   ├── style.css                   #   Design system (dark theme + print)
│   ├── luna_logo.png               #   Luna mascot logo
│   └── luna_logo_sm.png            #   Logo (small, for HTML embed)
├── run.py                          # CLI + OpenClaw Skill entry point
├── config.yaml                     # Global config (non-secret)
├── skill.yaml                      # OpenClaw Skill definition
├── requirements.txt                # Python dependencies
└── SKILL.md                        # Skill documentation
```

## Extending / 扩展指南

### Add a new data source / 新增数据源

```python
# brief/sources/my_source.py
from brief.sources.base import BaseSource
from brief.registry import register_source

@register_source("my_source")
class MySource(BaseSource):
    name = "my_source"

    async def fetch(self, since, until) -> list[Item]:
        # Your fetching logic here
        ...
```

### Add a new preset / 新增预设

```python
# In brief/presets.py
MY_PRESET = PresetConfig(
    name="my_preset",
    display_name="My Custom Report",
    cycle="weekly",
    editor_type="tech_weekly",
    sources=["my_source", "github"],
    ...
)
PRESETS["my_preset"] = MY_PRESET
```

### Add a custom middleware / 自定义中间件

```python
from brief.middleware import PipelineMiddleware, PipelineContext

class SlackNotifyMiddleware(PipelineMiddleware):
    def on_pipeline_end(self, ctx: PipelineContext):
        send_slack(f"Report #{ctx.issue_number} generated in {ctx.elapsed:.0f}s")

pipeline.use(SlackNotifyMiddleware())
```

## Tech Stack / 技术栈

- **Python 3.10+** — async/await, dataclasses, type hints
- **aiohttp** — async HTTP for parallel source fetching
- **Jinja2** — template rendering
- **WeasyPrint** — HTML → PDF (optional)
- **OpenAI-compatible API** — LLM content generation

## License

MIT

---

*LunaClaw Brief — where Luna holds the claws, and the claws hold the truth.* 🦞🐱
