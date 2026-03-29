"""Revise node — rewrites sections that failed grounding checks."""

from __future__ import annotations

import logging

from clawcat.llm import get_instructor_client, get_model, get_max_retries
from clawcat.schema.brief import BriefSection
from clawcat.state import PipelineState

logger = logging.getLogger(__name__)

REVISE_SYSTEM = """\
以下报告章节未通过质量检查，请修正后重写。

写作风格：{tone}
目标读者：{target_audience}
核心关注维度：
{focus_areas}

修正规则：
- 删除无法从源数据验证的日期/数字
- 确保所有实体名与源素材一致
- 保持原有结构（heading、section_type、items 格式）不变
- 每个条目 summary 控制在 80-200 字
- 使用中文撰写

原始章节（JSON）：
{section_json}

检查发现的问题：
{issues}
"""


def revise_node(state: PipelineState) -> dict:
    """Revise sections that failed grounding."""
    sections = state.get("checked_sections", [])
    retry_indices = state.get("retry_sections", [])
    task = state.get("task_config")
    check_issues = state.get("check_issues", {})

    if not retry_indices:
        return {"draft_sections": sections}

    focus_text = "\n".join(f"- {f}" for f in task.focus_areas) if task and task.focus_areas else "- 与主题相关"
    tone = task.tone if task else "professional"
    audience = task.target_audience if task else "general"

    client = get_instructor_client()

    revised = list(sections)
    for idx in retry_indices:
        if idx >= len(revised):
            continue

        section = revised[idx]
        issues_text = check_issues.get(idx, "Grounding check failures — verify all facts against sources")

        result = client.chat.completions.create(
            model=get_model(),
            response_model=BriefSection,
            messages=[
                {"role": "system", "content": REVISE_SYSTEM.format(
                    section_json=section.model_dump_json(),
                    issues=issues_text,
                    tone=tone,
                    target_audience=audience,
                    focus_areas=focus_text,
                )},
                {"role": "user", "content": f"Revise section: {section.heading}"},
            ],
            max_retries=get_max_retries(),
        )

        result.section_type = section.section_type
        revised[idx] = result
        logger.info("Revised section %d: %s", idx, section.heading)

    return {"draft_sections": revised}
