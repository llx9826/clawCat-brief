#!/usr/bin/env python3
"""
AI/CV Weekly - OpenClaw Skill 主入口（配置化版）

【优化点】
1. 统一配置管理（config.yaml + 环境变量）
2. 结构化日志
3. 并发安全的期号管理
4. 指数退避重试
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import config
from logger import setup_logger, get_logger
from issue_manager import IssueManager
from core.fetcher import DataFetcher
from core.filter import ItemFilter
from core.editor import WeeklyEditor
# 尝试使用 Jinja2 渲染器，如果失败则回退到旧版
try:
    from core.renderer_jinja2 import ReportRenderer
    print("✅ 使用 Jinja2 模板渲染器")
except ImportError:
    from core.renderer import ReportRenderer
    print("⚠️ 使用旧版渲染器（建议安装 Jinja2: pip install jinja2）")
from core.sender import EmailSender


class AICVWeeklySkill:
    """AI/CV Weekly Skill（配置化版）"""
    
    def __init__(self, override_config: Dict[str, Any] = None):
        self.override_config = override_config or {}
        
        # 从配置文件读取
        self.max_items = self.override_config.get("max_items", config.get("weekly.max_items", 35))
        self.time_range_days = self.override_config.get("time_range_days", config.get("weekly.time_range_days", 7))
        self.send_email = self.override_config.get("send_email", True)
        
        # 代理和 Token
        self.proxy = self.override_config.get("proxy", config.get_proxy())
        self.github_token = self.override_config.get("github_token", config.get_github_token())
        
        # 路径
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 期号管理器
        self.issue_manager = IssueManager(self.output_dir.parent)
        
        # 日志
        self.logger = get_logger("skill")
    
    async def run(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Skill 主入口"""
        if params:
            for key, value in params.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        print("="*60)
        print("🦞 AI/CV Weekly - 配置化版")
        print("="*60)
        print()
        
        now = datetime.now()
        time_range = f"{(now - timedelta(days=self.time_range_days)).strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
        
        self.logger.info("开始生成周报", extra={
            "extra_data": {
                "time_range": time_range,
                "proxy": bool(self.proxy),
                "github_token": bool(self.github_token),
                "max_items": self.max_items
            }
        })
        
        print(f"时间范围：{time_range}")
        print(f"代理：{self.proxy or '无'}")
        print(f"GitHub Token：{'已配置' if self.github_token else '未配置'}")
        print()
        
        try:
            # Layer 1: 数据提取
            print("【Layer 1】数据提取层...")
            async with DataFetcher(
                timeout=30,
                proxy=self.proxy,
                github_token=self.github_token
            ) as fetcher:
                fetch_result = await fetcher.fetch_all({
                    "time_range_days": self.time_range_days
                })
            
            items = fetch_result.get('items', [])
            sources_used = fetch_result.get('sources_used', [])
            failed_sources = fetch_result.get('failed_sources', [])
            
            print(f"   抓取到 {len(items)} 条")
            print(f"   成功源：{', '.join(sources_used)}")
            if failed_sources:
                print(f"   失败源：{', '.join(failed_sources)}")
            
            self.logger.info("数据抓取完成", extra={
                "extra_data": {
                    "total_items": len(items),
                    "sources_used": sources_used,
                    "failed_sources": failed_sources
                }
            })
            
            if len(items) < 3:
                return self._failure(f"数据不足（{len(items)} 条），无法生成周报")
            
            # 过滤层
            print("\n【过滤层】CV/OCR 优先...")
            item_filter = ItemFilter()
            selected = item_filter.filter_and_rank(items, max_keep=self.max_items)
            
            cv_count = sum(1 for i in selected if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR', 'Medical Imaging']))
            print(f"   精选 {len(selected)} 条")
            print(f"   CV/OCR 相关：{cv_count}/{len(selected)} 条（{cv_count/len(selected)*100:.0f}%）")
            
            if len(selected) < 3:
                return self._failure("过滤后内容不足")
            
            # Layer 2: 主编整合
            print("\n【Layer 2】主编整合层（指数退避重试）...")
            editor = WeeklyEditor()
            
            # 使用并发安全的期号管理
            issue_number = self.issue_manager.get_next_issue()
            
            result = editor.generate(selected, issue_number, max_retries=3)
            
            if not result.get('success'):
                self.logger.error("主编生成失败", extra={
                    "extra_data": {"error": result.get('error')}
                })
                return self._failure(f"主编生成失败：{result.get('error')}")
            
            markdown = result.get('markdown', '')
            quality_score = result.get('quality_score', 0)
            print(f"   ✅ 周报已生成（{len(markdown)} 字符）")
            print(f"   质量评分：{quality_score:.0%}")
            
            self.logger.info("周报内容生成完成", extra={
                "extra_data": {
                    "issue_number": issue_number,
                    "content_length": len(markdown),
                    "quality_score": quality_score
                }
            })
            
            # Layer 3: 数据渲染
            print("\n【Layer 3】数据渲染层...")
            renderer = ReportRenderer(self.output_dir)
            render_result = renderer.render(
                markdown, 
                issue_number, 
                time_range,
                stats={
                    "total_items": len(items),
                    "cv_count": cv_count,
                    "source_count": len(sources_used)
                }
            )
            
            html_path = render_result.get('html_path', '')
            md_path = render_result.get('md_path', '')
            print(f"   ✅ HTML 已保存：{html_path}")
            print(f"   ✅ Markdown 已保存：{md_path}")
            
            # 发送邮件
            if self.send_email:
                print("\n【邮件发送】...")
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                sender = EmailSender()
                subject = f"🦞 AI/CV Weekly - 第{issue_number}期"
                success = sender.send(subject, html_content, markdown[:1000] + "...")
                
                if success:
                    print("   ✅ 邮件已发送!")
                    self.logger.info("邮件发送成功")
                else:
                    print("   ⚠️ 邮件发送失败")
                    self.logger.warning("邮件发送失败")
            
            print()
            print("="*60)
            print("✅ 完成!")
            print("="*60)
            print()
            print(f"📊 统计:")
            print(f"   期号：第 {issue_number} 期")
            print(f"   原始数据：{len(items)} 条（{len(sources_used)} 个源）")
            print(f"   精选：{len(selected)} 条")
            print(f"   CV/OCR：{cv_count} 条（{cv_count/len(selected)*100:.0f}%）")
            print(f"   字数：{len(markdown)}")
            print(f"   质量：{quality_score:.0%}")
            
            self.logger.info("周报生成完成", extra={
                "extra_data": {
                    "issue_number": issue_number,
                    "html_path": html_path,
                    "stats": {
                        "total_items": len(items),
                        "cv_count": cv_count,
                        "content_length": len(markdown),
                        "quality_score": quality_score
                    }
                }
            })
            
            return {
                "status": "success",
                "issue_number": issue_number,
                "html_path": html_path,
                "md_path": md_path,
                "message": f"第 {issue_number} 期生成完成"
            }
            
        except Exception as e:
            self.logger.error("运行异常", extra={
                "extra_data": {"error": str(e)}
            }, exc_info=True)
            print(f"\n❌ 错误：{type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return self._failure(str(e))
    
    def _failure(self, message: str) -> Dict:
        """返回失败结果"""
        self.logger.error("周报生成失败", extra={"extra_data": {"message": message}})
        
        print()
        print("="*60)
        print("❌ 失败")
        print("="*60)
        print(f"原因：{message}")
        print()
        print("【原则】宁可缺，不要假")
        print("="*60)
        
        return {
            "status": "failed",
            "issue_number": None,
            "html_path": None,
            "message": message
        }


def main(override_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """OpenClaw Skill 入口"""
    # 初始化日志
    log_level = config.get("logging.level", "INFO")
    setup_logger(level=log_level)
    
    skill = AICVWeeklySkill(override_config)
    result = asyncio.run(skill.run())
    return result


if __name__ == "__main__":
    import json
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2))
