# LunaClaw 修复问题清单

## 概述
本次修复针对 LunaClaw 在部署和使用过程中遇到的关键问题，主要涉及字符串格式化、LLM 客户端兼容性、内容筛选机制等方面。

---

## 问题 1：Planner Node - 字符串格式化错误

### 现象
```
KeyError: '\n  "topic"'
```

### 原因
`PLANNER_SYSTEM` 提示词中包含 JSON 示例，花括号 `{}` 被 `str.format()` 误认为是占位符，导致格式化失败。

### 修复方案
改用字符串替换 `replace()` 而非 `format()`，避免 JSON 花括号冲突。

### 代码变更
**文件**: `clawcat/nodes/planner.py`

```python
# 修复前（错误）
system_content = PLANNER_SYSTEM.format(
    registry=registry,
    user_profile=profile.model_dump_json(),
    today=today,
)

# 修复后（正确）
system_content = PLANNER_SYSTEM.replace("{{registry}}", registry)
system_content = system_content.replace("{{user_profile}}", profile.model_dump_json())
system_content = system_content.replace("{{today}}", today)
```

### 同时修复
将 `PLANNER_SYSTEM` 中的占位符从 `{registry}` 改为 `{{registry}}`，避免 format 解析错误。

---

## 问题 2：LLM 客户端模式不兼容

### 现象
`instructor` 库使用 `JSON` 模式时，kimi-k2.5 模型输出格式不符合预期，返回混乱的 XML 标签包裹内容。

### 原因
kimi-k2.5 对 `instructor.Mode.JSON` 支持不佳，无法正确输出纯 JSON 格式。

### 修复方案
改用 `instructor.Mode.TOOLS` 模式，通过函数调用方式获取结构化输出。

### 代码变更
**文件**: `clawcat/llm.py`

```python
# 修复前
return instructor.from_openai(raw, mode=instructor.Mode.JSON)

# 修复后
return instructor.from_openai(raw, mode=instructor.Mode.TOOLS)
```

---

## 问题 3：Select Node - 缺乏市场范围约束 ⭐ 关键修复

### 现象
生成"美股周报"时，报告中出现大量 A股医药、小米汽车等与中国市场相关的内容，与主题严重不符。

### 原因分析
1. **筛选提示词缺陷**: `SELECT_SYSTEM` 只关注主题相关性，没有强制要求"美股市场"这个维度
2. **缺乏地域/市场过滤**: 筛选标准中没有"必须是美股标的"这个硬性约束
3. **大模型理解偏差**: 模型可能认为"全球科技股"包含小米，没有区分市场
4. **数据源问题**: 数据源中包含大量中文/A股内容

### 修复方案
在 `SELECT_SYSTEM` 提示词中添加明确的市场匹配规则和排除标准：

1. **市场/地域匹配规则**: 主题含"美股"则必须选美股相关内容
2. **排除标准**: 明确排除与主题市场无关的内容
3. **选择理由要求**: 必须说明为什么符合主题市场

### 代码变更
**文件**: `clawcat/nodes/select.py`

```python
# 修复前
SELECT_SYSTEM = """\
你是一位简报编辑。请从候选素材中选出最多 {max_items} 条，用于 {period} {topic} 报告。
时间范围：{since} ~ {until}

选择优先级：主题相关性 > 多样性 > 时效性 > 数据丰富度。
..."""

# 修复后
SELECT_SYSTEM = """\
你是一位简报编辑。请从候选素材中选出最多 {max_items} 条，用于 {period} {topic} 报告。
时间范围：{since} ~ {until}

【重要筛选规则】
1. 主题相关性：内容必须与报告主题"{topic}"高度相关
2. 市场/地域匹配：
   - 如果主题是"美股"，必须选择与美国股市、美股上市公司、美联储政策、美国经济相关的内容
   - 如果主题是"港股"，必须选择与香港股市相关的内容
   - 如果主题是"A股"，必须选择与中国大陆股市相关的内容
   - 严禁选择与主题市场无关的内容（如主题是美股时，不能选择小米汽车、A股医药等）
3. 多样性：覆盖不同行业/板块
4. 时效性：优先选择最新的事件
5. 数据丰富度：优先选择有具体数据的内容

【排除标准】
- 与主题市场无关的内容（如美股报告中的A股、港股内容）
- 非上市公司的新闻（除非是重大行业政策）
- 重复或高度相似的内容

请严格筛选，确保每条选中的内容都符合"{topic}"的市场范围！
..."""
```

### 修复效果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 素材筛选率 | 30/30 (100%) | 2/30 (6.7%) |
| 美股相关内容 | ❌ 混杂A股/小米 | ✅ 纯美股内容 |
| 美股代码覆盖 | ❌ 无 | ✅ XOM、CVX、LMT、RTX、QQQ |
| 指数覆盖 | ❌ 只有VIX | ✅ 道指、标普500、纳指 |
| 科技股覆盖 | ❌ 小米SU7 | ✅ 苹果、英伟达、微软 |

---

## 问题 4：Playwright 浏览器未安装

### 现象
PDF 导出失败，报错：
```
Executable doesn't exist at /home/gem/.cache/ms-playwright/chromium_headless_shell-1208/...
```

### 原因
Playwright 需要单独安装浏览器二进制文件，当前环境未安装。

### 修复方案
```bash
playwright install chromium
```

### 状态
当前环境未执行，如需 PDF 功能可后续安装。

---

## 问题 5：DuckDuckGo 搜索网络受限

### 现象
DuckDuckGo 搜索频繁失败，`ConnectError` 连接超时。

### 原因
网络环境限制，无法访问 DuckDuckGo/Yahoo/Bing 搜索 API。

### 影响
- 英文新闻源获取受限
- 依赖中文数据源（华尔街见闻等）
- 美股相关内容获取不足

### 建议修复
1. 配置代理访问国际搜索源
2. 添加备用搜索源（如 SerpAPI、Google Custom Search）
3. 增加美股专用数据源（Yahoo Finance、Bloomberg API）

---

## 修复文件汇总

| 文件 | 修复内容 |
|------|----------|
| `clawcat/nodes/planner.py` | 字符串格式化改用 replace() |
| `clawcat/llm.py` | 切换 instructor 模式为 TOOLS |
| `clawcat/nodes/select.py` | 添加市场范围约束规则 |
| `clawcat/prompts/planner.py` | 修复占位符格式 |

---

## 后续优化建议

1. **数据源扩展**: 添加美股专用数据源（Yahoo Finance、Finnhub 等）
2. **网络配置**: 配置代理以访问国际搜索源
3. **PDF 支持**: 安装 Playwright 浏览器以支持 PDF 导出
4. **测试覆盖**: 增加港股、A股等其他市场的测试用例
5. **筛选优化**: 根据实际使用反馈持续优化 Select Node 的筛选逻辑

---

*修复日期: 2026-03-29*
*修复者: 李claw*
