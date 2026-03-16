# 🦞 AI/CV Weekly

**AI/CV 领域周报生成器** - 专注 CV/OCR/多模态

---

## 快速开始

### 1. 配置邮箱（首次使用）

```bash
cd /home/gem/workspace/agent/workspace/skills/ai_cv_weekly
python -c "
import json
config = {
    'smtp_server': 'smtp.163.com',
    'smtp_port': 465,
    'sender_email': 'your_email@163.com',
    'sender_password': 'your_auth_code',
    'receiver_email': 'receiver@example.com',
    'use_ssl': true
}
with open('email_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"
```

### 2. 运行

```bash
openclaw skill run ai-cv-weekly
```

或

```bash
python run.py
```

---

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   抓取数据   │ ──→ │ 过滤排序     │ ──→ │ 主编模式    │ ──→ │ 邮件发送    │
│  GitHub    │     │ CV/OCR 优先   │     │ 单次 LLM    │     │             │
│  arXiv     │     │ 低价值剔除   │     │ 完整周报    │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
```

---

## 核心模块

### core/fetcher.py - 数据抓取
- GitHub Trending
- arXiv AI/CV

### core/filter.py - 过滤排序
- CV/OCR 关键词优先
- 低价值内容剔除
- 领域标签分配

### core/editor.py - 主编模式
- 单次 LLM 调用生成完整周报
- 有观点、有判断、有批判
- 禁止空话模板

### core/sender.py - 邮件发送
- SMTP 发送
- HTML + 纯文本

---

## 配置说明

### run.py 参数

```python
{
    "llm_mode": "required",      # required/optional
    "max_items": 15,              # 最大选取条目数
    "time_range_days": 7,         # 抓取时间范围
    "send_email": true            # 是否发送邮件
}
```

### 环境变量

无特殊环境变量要求。

---

## 输出示例

### HTML 周报
保存在 `output/weekly_YYYYMMDD_HHMMSS.html`

### Markdown 备份
保存在 `output/weekly_YYYYMMDD_HHMMSS.md`

### 邮件
主题：`🦞 AI/CV Weekly - 第 X 期`

---

## 常见问题

### Q: LLM 不可用怎么办？
A: 默认模式（required）会终止生成，确保内容质量。如需降级模式，设置 `llm_mode: "optional"`。

### Q: 如何修改 CV/OCR 优先级？
A: 编辑 `core/filter.py` 中的 `cv_keywords` 字典。

### Q: 邮件发送失败？
A: 检查 `email_config.json` 配置，确认授权码正确。

---

## 开发

### 目录结构

```
ai_cv_weekly/
├── skill.yaml
├── SKILL.md
├── README.md
├── run.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── fetcher.py
│   ├── filter.py
│   ├── editor.py
│   └── sender.py
├── output/
├── memory/
├── llm_client.py
└── email_config.json
```

### 测试

```bash
python run.py
```

---

## 更新日志

### v2.0.0 (2026-03-12)
- ✅ 简化架构，合并冗余模块
- ✅ 主编模式：单次 LLM 生成完整周报
- ✅ CV/OCR 优先过滤
- ✅ Fail closed 机制

### v1.0.0 (2026-03-11)
- 初始版本

---

## 许可证

MIT License

---

**🦞 主编**: 李 claw  
**📬 反馈**: 欢迎提出建议
