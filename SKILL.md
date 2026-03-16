---
name: ai-cv-weekly
description: |
  AI/CV Weekly 周报自动生成器
  专注 CV/OCR/多模态领域，一键生成专业周报
version: 2.1.0
author: 李 claw
---

# 🦞 AI/CV Weekly

AI/CV 领域周报自动生成 Skill，专注 CV/OCR/多模态领域。

## 核心理念

> **宁可缺，不要假**

- 规则层只做筛选、分类、标签、排序
- 正式正文由 LLM 一次性生成（主编模式）
- LLM 不可用时 fail closed
- 不允许硬凑行业动态
- 不允许模板冒充内容

## 数据源

- **90+ RSS 源** - Karpathy 推荐的顶级技术博客
- **GitHub** - 热门 CV/OCR 开源项目
- **arXiv** - 最新学术论文
- **技术媒体** - Hacker News、Dev.to 等

## 使用方式

### 方式 1: 命令触发

```
生成 AI/CV 周报
```

### 方式 2: 定时任务

每周一上午 9 点自动生成

### 方式 3: 代码调用

```python
from skills.ai_cv_weekly.run import main

result = main({
    "send_email": True,
    "time_range_days": 7
})
```

## 输出

- HTML 格式周报（邮件发送）
- Markdown 格式（存档）
- 数据仪表盘统计

## 配置

复制 `config.yaml` 为 `config.local.yaml` 并填写：

```yaml
llm:
  api_key: your_api_key
  
email:
  sender_email: your_email@163.com
  sender_password: your_auth_code
  receiver_email: receiver@example.com
```

## 许可证

MIT License
