#!/usr/bin/env python3
"""
AI/CV Weekly - Layer 2: 主编整合层（指数退避重试版）

【优化点】
1. 针对 Kimi 256K 上下文优化（精简输入）
2. 强化 CV/OCR 侧重
3. 添加输出质量检查
4. 指数退避重试机制
"""

import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_client import LLMClient


class WeeklyEditor:
    """周报主编（指数退避重试版）"""
    
    def __init__(self):
        self.llm_client = None
        self.llm_available = False
    
    def connect_llm(self) -> bool:
        """连接 LLM"""
        try:
            self.llm_client = LLMClient()
            response = self.llm_client.chat(
                [{"role": "user", "content": "OK"}],
                max_tokens=10
            )
            self.llm_available = bool(response)
            if self.llm_available:
                print("✅ LLM 已连接 (Kimi K2.5)")
            return self.llm_available
        except Exception as e:
            print(f"❌ LLM 连接失败：{e}")
            return False
    
    def _exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        计算指数退避延迟时间
        
        Args:
            attempt: 当前重试次数（从0开始）
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
        
        Returns:
            float: 延迟时间（秒）
        """
        # 指数退避：2^attempt * base_delay + 随机抖动
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0, delay * 0.1)  # 10% 随机抖动
        return delay + jitter
    
    def generate(self, items: List[Dict], issue_number: int, max_retries: int = 3) -> Dict:
        """
        生成完整周报（带重试）
        
        【Kimi 优化】
        - 精简输入：只取 Top 15，描述限制 150 字
        - 强化 CV/OCR 标签
        - 输出质量检查
        """
        # 检查数据量
        if len(items) < 3:
            return {
                "success": False,
                "markdown": None,
                "error": f"数据不足（{len(items)} 条）"
            }
        
        # 连接 LLM
        if not self.llm_available:
            if not self.connect_llm():
                return {"success": False, "error": "LLM 不可用"}
        
        # 准备数据（Kimi 优化：精简输入）
        prepared_items = self._prepare_items_for_kimi(items)
        
        # 构建 prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prepared_items, issue_number)
        
        print(f"📝 生成周报（{len(prepared_items)} 条内容，Kimi 优化）...")
        
        # 指数退避重试机制
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.llm_client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=8000  # 增加到 8000 tokens
                )
                
                if not response:
                    last_error = "LLM 返回为空"
                    if attempt < max_retries:
                        delay = self._exponential_backoff(attempt)
                        print(f"   LLM 返回为空，{delay:.1f}秒后重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                        continue
                    return {"success": False, "error": last_error}
                
                # 质量检查
                quality_check = self._check_quality(response)
                if not quality_check["pass"]:
                    last_error = f"质量检查失败：{quality_check['reason']}"
                    if attempt < max_retries:
                        delay = self._exponential_backoff(attempt)
                        print(f"   {last_error}，{delay:.1f}秒后重试...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"   ⚠️ 质量检查未通过，但已达到最大重试次数，使用当前结果")
                
                markdown = self._extract_markdown(response)
                
                return {
                    "success": True,
                    "markdown": markdown,
                    "quality_score": quality_check.get("score", 0),
                    "error": None
                }
                
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    delay = self._exponential_backoff(attempt)
                    print(f"   异常：{last_error[:50]}，{delay:.1f}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    return {"success": False, "error": last_error}
        
        return {"success": False, "error": f"超过最大重试次数，最后错误：{last_error}"}
    
    def _prepare_items_for_kimi(self, items: List[Dict]) -> List[Dict]:
        """
        为 Kimi 准备数据（充足输入，确保 5000+ 字输出）
        
        【优化】
        - 取 Top 40 条（保证素材充足）
        - 描述限制 500 字（给 LLM 更多上下文）
        - 保留完整标题
        - 强化 CV/OCR 标签
        """
        # 按 CV/OCR 相关度排序
        cv_items = [i for i in items if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR', 'Medical Imaging'])]
        multimodal_items = [i for i in items if 'Multimodal' in i.get('domain_tags', [])]
        other_items = [i for i in items if i not in cv_items and i not in multimodal_items]
        
        # 取 Top 25（避免输出被截断）
        top_items = (cv_items + multimodal_items + other_items)[:25]
        
        # 保留更完整的描述
        prepared = []
        for item in top_items:
            raw_text = item.get('raw_text', '')
            # 如果原始内容很长，取前 500 字；如果很短，保留全部
            if len(raw_text) > 500:
                raw_text = raw_text[:500] + "..."
            
            prepared.append({
                "title": item.get('title', ''),  # 保留完整标题
                "source": item.get('source_name', item.get('source', 'unknown')),
                "url": item.get('url', '#'),
                "domain_tags": item.get('domain_tags', []),
                "raw_text": raw_text,  # 500 字描述
                "stars": item.get('meta', {}).get('stars', 0),
            })
        
        return prepared
    
    def _build_system_prompt(self) -> str:
        """构建系统 prompt（Kimi 优化版 + 中文翻译）"""
        return """你是 AI/CV Weekly 的主编，有 10 年科技媒体经验，专注于计算机视觉（CV）、OCR、多模态 AI 领域。

【核心原则】
1. 基于真实数据写作，不编造内容
2. 信息不足就说"需要进一步观察"
3. 禁止空话："值得关注"、"具有重要意义"、"推动行业发展"
4. 禁止模板化表达
5. 侧重 CV/OCR/多模态（必须占 50% 以上内容）

【翻译要求 - 重要】
1. 除专有名词外，所有内容必须翻译成中文
2. 专有名词保留英文，首次出现时中文解释（如：Transformer（变换器模型））
3. GitHub 项目介绍翻译成流畅中文
4. 论文摘要翻译成学术中文
5. 技术术语保留英文，但需中文解释

【专有名词白名单 - 保留英文】
- 项目名：PaddleOCR、MMDetection、Transformers、OpenCV、Tesseract 等
- 技术术语：Transformer、CNN、RNN、BERT、GPT、OCR、CV、LLM 等
- 会议名：CVPR、ICCV、ECCV、NeurIPS、ICML、ACL 等
- 公司/机构名：OpenAI、Google、Meta、DeepMind、百度、阿里 等
- 编程语言/框架：Python、PyTorch、TensorFlow、Keras 等

【写作风格】
- 像给人讲解，不是填模板
- 可以有观点、有判断、有批判
- 锐评要有锋芒，说明潜在问题
- 不允许中性评论（"既...又..."）

【周报结构 - 强制要求全部 6 个章节，6000 字以上】

必须使用以下章节标题格式（严格按照这个格式）：
## 一、本周核心结论
## 二、本周重点事件  
## 三、开源项目推荐
## 四、论文推荐
## 五、本周趋势分析
## 六、🦞 Claw 复盘

每个章节的内容要求：
1. **一、本周核心结论**（5-8 条 bullet points，每条 50-80 字，深入分析，不要只罗列）
2. **二、本周重点事件**（5-8 条，每条 200-300 字详细描述，包含背景、影响、意义）
3. **三、开源项目推荐**（5-8 个，每个项目必须包含以下结构）：
   - **是什么**：项目简介，核心功能
   - **解决什么问题**：具体痛点、应用场景
   - **相比其他方案的优势**：技术特点、性能对比、创新点
   - **🦞 Claw 锐评**：100-150 字批判性点评
4. **四、论文推荐**（4-6 篇，每篇论文必须包含以下结构）：
   - **是什么**：论文标题、作者、机构
   - **解决什么问题**：研究背景、现有方法缺陷
   - **核心创新点**：方法概述、技术优势、实验结果
   - **相比其他方案的优势**：与 SOTA 对比、突破点
   - **🦞 Claw 锐评**：100-150 字批判性点评
5. **五、本周趋势分析**（5-8 个趋势，每个 150-200 字深入分析，基于具体内容）
6. **六、🦞 Claw 复盘**（800-1000 字，有深度、有观点、有批判，总结本周整体观察）

【字数要求 - 强制】
- 总字数必须达到 6000 字以上
- 每个章节都要充实，不能跳过任何章节
- 基于提供的素材充分展开，不要惜墨
- 如果某类内容不足，就基于现有内容深入分析，不能省略该章节

【CV/OCR 侧重要求】
- 必须优先分析 CV/OCR 相关内容
- 纯 LLM/Agent 内容简略带过
- 多模态内容要强调视觉部分

【锐评要求 - 统一格式】
- 必须说明潜在问题或局限
- 可以批判，但要有理有据
- 不 PR 腔，不吹捧
- 统一格式：`**🦞 Claw 锐评**：内容`（所有锐评必须用这个格式）

【论文锐评要求】
- 论文也必须带锐评，格式同样是 `**🦞 Claw 锐评**：内容`
- 不要只写"点评"，必须用"Claw 锐评"

【复盘要求】
- 将"主编复盘"改为"**🦞 Claw 复盘**"
- 格式与锐评一致，有观点、有判断

输出 Markdown 格式。"""
    
    def _build_user_prompt(self, items: List[Dict], issue_number: int) -> str:
        """构建用户 prompt（精简版）"""
        now = datetime.now()
        last_week = now.strftime("%Y-%m-%d")
        last_week_prev = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 统计 CV/OCR 占比
        cv_count = sum(1 for i in items if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR']))
        
        prompt = f"""请生成第 {issue_number} 期 AI/CV Weekly 周报。

**时间范围**: {last_week_prev} ~ {last_week}
**内容统计**: {len(items)} 条（CV/OCR 相关：{cv_count} 条）

**本周内容**:

"""
        
        for i, item in enumerate(items, 1):
            tags = ', '.join(item.get('domain_tags', []))
            stars = item.get('stars', 0)
            stars_str = f" ⭐{stars}" if stars else ""
            
            prompt += f"""{i}. **{item['title']}**{stars_str}
   来源：{item['source']} | 领域：{tags}
   {item['raw_text']}

"""
        
        prompt += f"""
【生成要求 - 强制完成全部 6 章节】:
1. **必须包含全部 6 个章节**，缺一不可，这是最高优先级
2. **字数控制**：总字数 4000-6000 字，确保内容完整不被截断
3. CV/OCR 内容必须占 50% 以上
4. 每个项目/论文的描述要精炼，避免过长：
   - 是什么：50-80 字
   - 解决什么问题：50-80 字
   - 核心创新点：80-120 字
   - 相比其他方案的优势：50-80 字
   - 锐评：80-120 字
5. **章节内容数量**：
   - 核心结论：5-6 条
   - 重点事件：4-5 条
   - 开源项目：4-5 个
   - 论文推荐：4-5 篇（如果论文素材不足，就从项目中挑选最有技术深度的作为补充）
   - 趋势分析：5-6 条
   - Claw 复盘：600-800 字
6. **六、🦞 Claw 复盘** 必须完整写完，不要截断
7. **格式规范**：
   - 严格按照上面指定的章节标题格式
   - 章节之间用空行分隔

【重要提醒 - 必须遵守】
你收到了 {len(items)} 条内容素材，请合理分配：
- 精选最优质的 4-5 个 GitHub 项目用于"开源项目推荐"
- 精选最优质的 4-5 篇论文用于"论文推荐"（如果论文不足，就用技术项目补充）
- 所有内容用于"趋势分析"和"Claw 复盘"
- **必须生成全部 6 个章节，且复盘必须完整**，这是强制要求

请生成周报（5000 字以上）："""
        
        return prompt
    
    def _check_quality(self, response: str) -> Dict:
        """
        质量检查（严格版）
        
        【检查项】
        - 字数是否足够（6000+）
        - 必须包含全部 6 个章节
        - 必须包含锐评和复盘
        """
        # 检查章节存在（支持多种格式）
        chapter_patterns = {
            "core_conclusion": ["核心结论", "一、核心结论", "一、本周核心结论"],
            "key_events": ["重点事件", "二、重点事件", "二、本周重点事件"],
            "projects": ["开源项目", "三、开源项目", "三、开源项目推荐"],
            "papers": ["论文", "四、论文", "四、论文推荐"],
            "trends": ["趋势", "趋势分析", "五、趋势", "五、趋势分析", "五、本周趋势"],
            "review": ["复盘", "Claw 复盘", "六、复盘", "六、Claw 复盘", "主编复盘"],
        }
        
        chapter_checks = {}
        for chapter_name, patterns in chapter_patterns.items():
            found = any(p in response for p in patterns)
            chapter_checks[f"has_{chapter_name}"] = found
        
        # 其他检查
        other_checks = {
            "min_length": len(response) >= 6000,  # 提高到 6000 字
            "has_commentary": "🦞" in response and "锐评" in response,
            "has_enough_items": response.count("###") >= 10,  # 至少 10 个项目/论文
        }
        
        all_checks = {**chapter_checks, **other_checks}
        score = sum(all_checks.values()) / len(all_checks)
        
        # 严格检查：所有章节必须都存在
        missing_chapters = [k.replace("has_", "") for k, v in chapter_checks.items() if not v]
        
        if missing_chapters:
            return {
                "pass": False,
                "reason": f"缺少章节: {', '.join(missing_chapters)}",
                "score": score
            }
        
        if score < 0.8:
            failed = [k for k, v in all_checks.items() if not v]
            return {
                "pass": False,
                "reason": f"质量不足: {', '.join(failed)}",
                "score": score
            }
        
        return {"pass": True, "score": score}
    
    def _extract_markdown(self, response: str) -> str:
        """提取 Markdown"""
        # 移除代码块标记
        if response.startswith('```markdown'):
            response = response[11:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        
        return response.strip()
