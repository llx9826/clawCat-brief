# AI/CV Weekly Agent 会话记忆

## 会话信息

- **Session Key**: main-session
- **创建时间**: 2026-03-12
- **人格**: AI/CV Weekly 编辑（专业、高效、数据驱动）
- **记忆目录**: /home/gem/workspace/agent/workspace/skills/ai_cv_weekly/memory/

## 记忆结构

```
memory/
├── SESSION.md          # 会话元信息（本文件）
├── 2026-03-12.md       # 今日工作记录
├── data/              # 数据缓存
│   ├── raw/           # 原始抓取数据
│   ├── filtered/      # 过滤后数据
│   └── weekly/        # 周报历史
├── sources/           # 数据源状态
│   └── health.json    # 源健康度
└── learnings/         # 学习记录
    ├── ERRORS.md
    ├── LEARNINGS.md
    └── IMPROVEMENTS.md
```

## 当前状态

- **状态**: 活跃
- **最后活跃**: 2026-03-12 22:32
- **本期期号**: 35
- **数据源**: 90+ RSS 源 + GitHub + arXiv

## 核心记忆

### 数据源状态
- **Karpathy RSS**: 69/90 源正常
- **GitHub**: API 正常
- **arXiv**: 正常

### 用户偏好
- 周报发送时间: 每周一上午 9 点
- 邮件接收: llx9826@163.com
- 数据量: 35 条精选

### 最近问题
- ✅ LLM API key 已修复
- ✅ Claw 复盘正常生成
- ⚠️ 机器之心/36氪 Web Search 待优化

### 改进计划
1. SQLite 数据持久化
2. 主题系统
3. 更多数据源
