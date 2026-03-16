#!/usr/bin/env python3
"""
AI/CV Weekly - 全局配置

【反伪动态治理核心原则】
1. 宁可缺，不要假
2. 宁可失败，不要用模板冒充 LLM 结果
3. 规则层只能做筛选、分类、标签、排序，不能写正式正文
4. 正式正文必须由 LLM 生成
5. LLM 不可用时 fail closed，不允许继续生成
"""

from typing import Dict, Any
from pathlib import Path
import json


class GenerationMode:
    """生成模式"""
    REQUIRED = "required"      # 强制 LLM，失败即终止
    OPTIONAL = "optional"      # LLM 可选，允许 fallback（不推荐）
    DEBUG = "debug"            # 调试模式，允许模板（仅本地测试）


# ========== 核心配置 ==========

# LLM 生成模式：强制 LLM，失败即终止
LLM_GENERATION_MODE = GenerationMode.REQUIRED

# 是否允许模板 fallback（正式环境必须为 False）
ALLOW_TEMPLATE_FALLBACK = False

# 是否允许硬凑行业动态
ALLOW_FAKING_INDUSTRY_NEWS = False

# 行业动态最小数量（不强制满足，真实不足时允许为空）
INDUSTRY_NEWS_TARGET_MIN = 0  # 不强制

# 发布门禁：必须全部满足才允许发布
PUBLISH_GATE_REQUIREMENTS = {
    "llm_must_be_available": True,
    "all_body_text_from_llm": True,
    "claw_summary_from_llm": True,
    "no_template_commentary": True,
    "industry_news_must_be_real": True,
    "no_category_faking": True,
}

# ========== 真实行业来源白名单 ==========

# 只有这些来源的内容才能被标记为 industry_news
REAL_INDUSTRY_SOURCES = {
    # 大厂官方博客
    "openai_blog",
    "openai",
    "deepmind_blog",
    "deepmind",
    "meta_ai",
    "meta",
    "anthropic",
    "nvidia",
    "nvidia_blog",
    "google_ai",
    "google_blog",
    "microsoft_ai",
    
    # 知名科技媒体
    "techcrunch",
    "mit_technology_review",
    "mit technology review",
    "the_information",
    "wired",
    "the_verge",
    
    # VC/投资机构
    "a16z",
    "sequoia",
    
    # 社区平台官方
    "huggingface",
    "huggingface_blog",
}

# 行业动态关键词（必须配合真实来源使用）
INDUSTRY_NEWS_KEYWORDS = [
    "raises", "funding", "series a", "series b", "series c",
    "acquisition", "acquires", "launches", "announces", "release",
    "released", "debut", "official blog", "new model", "new product",
    "partnership", "investment", "valuation", "unveils",
    "model release", "dataset release"
]

# ========== LLM 配置 ==========

LLM_CONFIG = {
    "provider": "bailian",
    "model": "qwen3.5-plus",
    "timeout_seconds": 60,
    "max_retries": 2,
    "temperature": 0.7,
}

# ========== 失败状态定义 ==========

class FailureStatus:
    """失败状态码"""
    SUCCESS = "success"
    LLM_UNAVAILABLE = "llm_unavailable"
    LLM_REQUIRED_BUT_UNAVAILABLE = "llm_required_but_unavailable"
    LLM_CALL_FAILED = "llm_call_failed"
    LLM_RETURNED_EMPTY = "llm_returned_empty"
    LLM_JSON_INVALID = "llm_json_invalid"
    PUBLISH_GATE_FAILED = "publish_gate_failed"
    INDUSTRY_NEWS_FAKING_DETECTED = "industry_news_faking_detected"
    TEMPLATE_FALLBACK_DETECTED = "template_fallback_detected"


def load_config_from_file(config_path: str = None) -> Dict[str, Any]:
    """从文件加载配置（可选覆盖）"""
    if config_path is None:
        config_path = Path(__file__).parent / "generation_config.json"
    
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config_to_file(config: Dict[str, Any], config_path: str = None):
    """保存配置到文件"""
    if config_path is None:
        config_path = Path(__file__).parent / "generation_config.json"
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


# ========== 默认配置（用于初始化） ==========

DEFAULT_CONFIG = {
    "llm_generation_mode": GenerationMode.REQUIRED,
    "allow_template_fallback": False,
    "allow_faking_industry_news": False,
    "industry_news_target_min": 0,
    "publish_gate_requirements": PUBLISH_GATE_REQUIREMENTS,
    "real_industry_sources": list(REAL_INDUSTRY_SOURCES),
    "llm_config": LLM_CONFIG,
}
