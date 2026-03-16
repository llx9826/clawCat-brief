#!/usr/bin/env python3
"""
AI/CV Weekly - Layer 3: 数据渲染层（海报级设计版）

【设计特点】
1. 现代玻璃态设计
2. 丰富色块系统
3. 渐变色彩搭配
4. 动态视觉效果
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class ReportRenderer:
    """报告渲染器（海报级设计）"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def render(self, markdown: str, issue_number: int, time_range: str, 
               stats: Dict = None) -> Dict:
        """渲染报告（海报级设计）"""
        # 解析 Markdown
        sections = self._parse_markdown(markdown)
        
        # 生成海报级 HTML
        html = self._generate_poster_html(sections, issue_number, time_range, stats)
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"weekly_{timestamp}.html"
        md_path = self.output_dir / f"weekly_{timestamp}.md"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return {"html": html, "html_path": str(html_path), "md_path": str(md_path)}
    
    def _parse_markdown(self, markdown: str) -> List[Dict]:
        """解析 Markdown 结构"""
        sections = []
        lines = markdown.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('## '):
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content),
                        'type': self._detect_section_type(current_section)
                    })
                current_section = line[3:].strip()
                current_content = []
            elif line.strip():
                current_content.append(line)
        
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content),
                'type': self._detect_section_type(current_section)
            })
        
        return sections
    
    def _detect_section_type(self, title: str) -> str:
        """检测章节类型"""
        if '核心结论' in title:
            return 'conclusions'
        elif '重点事件' in title:
            return 'events'
        elif '开源项目' in title:
            return 'projects'
        elif '论文' in title:
            return 'papers'
        elif '趋势' in title:
            return 'trends'
        elif '复盘' in title:
            return 'editor_note'
        return 'content'
    
    def _generate_poster_html(self, sections: List[Dict], issue_number: int, 
                              time_range: str, stats: Dict) -> str:
        """生成海报级 HTML"""
        now = datetime.now()
        total_items = stats.get('total_items', 0) if stats else 0
        cv_count = stats.get('cv_count', 0) if stats else 0
        source_count = stats.get('source_count', 0) if stats else 0
        
        content_html = self._render_sections(sections)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI/CV Weekly - 第{issue_number}期</title>
    <style>
        /* ===== 设计系统 - 安全色 ===== */
        :root {{
            --primary: #4f46e5;
            --accent-amber: #f59e0b;
            --bg-light: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #475569;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 16px;  /* 手机端基础字号 */
            line-height: 1.6;
            color: #1e293b;
            background: #f1f5f9;
            min-height: 100vh;
            padding: 0;
            margin: 0;
        }}
        
        @media (min-width: 768px) {{
            body {{
                font-size: 15px;  /* 电脑端稍小 */
                line-height: 1.7;
            }}
        }}
        
        /* ===== 容器 - 响应式 ===== */
        .container {{
            width: 100%;
            max-width: 680px;  /* 手机端更宽，电脑端适中 */
            margin: 0 auto;
            padding: 16px;
            box-sizing: border-box;
        }}
        
        @media (min-width: 768px) {{
            .container {{
                max-width: 760px;  /* 平板 */
                padding: 24px;
            }}
        }}
        
        @media (min-width: 1024px) {{
            .container {{
                max-width: 900px;  /* 电脑 */
                padding: 32px;
            }}
        }}
        
        /* ===== 头部 - 简洁白色 ===== */
        header {{
            background: #ffffff;
            padding: 40px 32px;
            border-radius: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 5px solid #f59e0b;
        }}
        
        .logo {{
            font-size: 64px;
            margin-bottom: 20px;
            animation: float 3s ease-in-out infinite;
            filter: drop-shadow(0 4px 8px rgba(245,158,11,0.3));
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0) rotate(0deg); }}
            50% {{ transform: translateY(-12px) rotate(5deg); }}
        }}
        
        header h1 {{
            font-size: 40px;
            font-weight: 800;
            color: #f59e0b;
            margin-bottom: 12px;
            letter-spacing: -1px;
        }}
        
        header .subtitle {{
            color: #92400e;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 8px;
        }}
        
        /* ===== 数据仪表盘 - 彩色卡片 ===== */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 32px;
        }}
        
        .stat-card {{
            background: white;
            padding: 28px 20px;
            border-radius: 24px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            border-top: 5px solid;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 20px -5px rgba(0,0,0,0.15);
        }}
        
        .stat-card:nth-child(1) {{ border-top-color: #f59e0b; }}
        .stat-card:nth-child(2) {{ border-top-color: #22c55e; }}
        .stat-card:nth-child(3) {{ border-top-color: #6366f1; }}
        
        .stat-number {{
            font-size: 40px;
            font-weight: 900;
            background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #64748b;
            margin-top: 8px;
            font-weight: 500;
        }}
        
        /* ===== 内容卡片 - 响应式 ===== */
        .content-card {{
            background: white;
            padding: 24px 20px;  /* 手机端更紧凑 */
            border-radius: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: 1px solid #e2e8f0;
        }}
        
        @media (min-width: 768px) {{
            .content-card {{
                padding: 32px 28px;
                border-radius: 24px;
            }}
        }}
        
        @media (min-width: 1024px) {{
            .content-card {{
                padding: 40px 32px;
                border-radius: 28px;
            }}
        }}
        
        /* ===== 章节标题 - 响应式 ===== */
        h2 {{
            font-size: 22px;  /* 手机端 */
            font-weight: 700;
            margin: 32px 0 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid #f59e0b;
            color: #1e293b;
        }}
        
        @media (min-width: 768px) {{
            h2 {{
                font-size: 26px;
                margin: 40px 0 24px;
            }}
        }}
        
        h2:first-child {{
            margin-top: 0;
        }}
        
        h3 {{
            font-size: 22px;
            font-weight: 700;
            margin: 32px 0 16px;
            color: #1e293b;
        }}
        
        /* ===== 项目卡片 - 彩色左边框 ===== */
        .project-card {{
            background: linear-gradient(135deg, #ffffff 0%, #fefce8 100%);
            border-radius: 24px;
            padding: 32px;
            margin: 24px 0;
            border-left: 6px solid #f59e0b;
            box-shadow: 
                0 10px 15px -3px rgba(0,0,0,0.1),
                0 4px 6px -2px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}
        
        .project-card:hover {{
            transform: translateX(8px);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.15);
        }}
        
        .project-card.paper {{
            border-left-color: #6366f1;
            background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
        }}
        
        /* ===== 锐评卡片 - 醒目黄色 ===== */
        .claw-commentary {{
            background: linear-gradient(135deg, #fef9c3 0%, #fde047 100%);
            border: 3px solid #facc15;
            border-radius: 24px;
            padding: 28px 32px;
            margin: 28px 0;
            box-shadow: 
                0 10px 15px -3px rgba(250, 204, 21, 0.4),
                inset 0 2px 4px rgba(255,255,255,0.6);
            position: relative;
        }}
        
        .claw-commentary::before {{
            content: '🦞';
            font-size: 32px;
            position: absolute;
            top: -16px;
            left: 24px;
            background: #fef9c3;
            padding: 4px 12px;
            border-radius: 12px;
            border: 2px solid #facc15;
        }}
        
        .claw-header {{
            font-weight: 800;
            color: #92400e;
            font-size: 16px;
            margin-bottom: 16px;
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .claw-commentary p {{
            color: #78350f;
            font-style: italic;
            font-weight: 500;
            line-height: 1.8;
            margin: 0;
        }}
        
        /* ===== 列表样式 ===== */
        ul {{
            margin: 20px 0;
            padding-left: 28px;
        }}
        
        li {{
            margin: 14px 0;
            color: #475569;
            line-height: 1.8;
            position: relative;
        }}
        
        li::marker {{
            color: #f59e0b;
            font-size: 1.2em;
        }}
        
        /* ===== 链接样式 ===== */
        a {{
            color: #f97316;
            text-decoration: none;
            font-weight: 600;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }}
        
        a:hover {{
            border-bottom-color: #f97316;
        }}
        
        /* ===== 底部 ===== */
        footer {{
            text-align: center;
            padding: 48px 32px;
            color: #92400e;
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(254,243,199,0.8) 100%);
            border-radius: 32px;
            margin-top: 32px;
            border: 2px solid rgba(245,158,11,0.3);
        }}
        
        .footer-logo {{
            font-size: 48px;
            margin-bottom: 16px;
            animation: float 3s ease-in-out infinite;
        }}
        
        footer p {{
            margin: 6px 0;
            font-size: 15px;
            font-weight: 500;
        }}
        
        /* ===== 响应式 ===== */
        @media (max-width: 768px) {{
            .container {{ padding: 16px; }}
            header {{ padding: 32px 24px; }}
            header h1 {{ font-size: 32px; }}
            .dashboard {{ grid-template-columns: 1fr; }}
            .content-card {{ padding: 24px; }}
            .project-card {{ padding: 24px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <header>
            <div class="logo">🦞</div>
            <h1>AI/CV Weekly</h1>
            <p class="subtitle">专注 CV/OCR/多模态领域 · 第 {issue_number} 期</p>
            <p style="color: #a16207; font-size: 15px;">{time_range}</p>
            
            <!-- 数据仪表盘 -->
            <div class="dashboard">
                <div class="stat-card">
                    <div class="stat-number">{total_items}</div>
                    <div class="stat-label">原始数据</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{cv_count}</div>
                    <div class="stat-label">CV/OCR 相关</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{source_count}</div>
                    <div class="stat-label">数据源</div>
                </div>
            </div>
        </header>
        
        <!-- 内容 -->
        <div class="content-card">
            {content_html}
        </div>
        
        <!-- 底部 -->
        <footer>
            <div class="footer-logo">🦞</div>
            <p><strong>AI/CV Weekly</strong> - 主编模式</p>
            <p>专注 CV/OCR/多模态领域 · 真实数据生成</p>
            <p style="margin-top: 12px; opacity: 0.8;">生成时间: {now.strftime("%Y-%m-%d %H:%M")}</p>
        </footer>
    </div>
</body>
</html>"""
    
    def _render_sections(self, sections: List[Dict]) -> str:
        """渲染章节内容"""
        html_parts = []
        
        for section in sections:
            section_type = section.get('type', 'content')
            title = section.get('title', '')
            content = section.get('content', '')
            
            # 章节标题
            html_parts.append(f'<h2>{title}</h2>')
            
            # 根据类型渲染
            if section_type in ['projects', 'papers']:
                html_parts.append(self._render_project_cards(content, section_type))
            else:
                html_parts.append(self._render_content(content))
        
        return '\n'.join(html_parts)
    
    def _render_project_cards(self, content: str, section_type: str) -> str:
        """渲染项目/论文卡片"""
        html = content
        
        # 将 ### 标题转换为卡片
        html = re.sub(
            r'### (.+?)\n',
            lambda m: f'<div class="project-card {section_type}"><h3>{m.group(1)}</h3>',
            html
        )
        
        # 闭合卡片（在下一个 ### 或章节结束前）
        html = re.sub(r'(</div>|\n\n)(?=<h|</div>|$)', r'</div>\1', html)
        
        # 锐评转换为黄色卡片
        html = re.sub(
            r'\*\*🦞 Claw 锐评\*\*：(.*?)(?=\n\n|</div>|$)',
            r'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>\1</p></div>',
            html,
            flags=re.DOTALL
        )
        
        # 兼容旧格式
        html = re.sub(
            r'\*\*点评\*\*：(.*?)(?=\n\n|</div>|$)',
            r'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>\1</p></div>',
            html,
            flags=re.DOTALL
        )
        
        return html
    
    def _render_content(self, content: str) -> str:
        """渲染普通内容"""
        html = content
        
        # 过滤所有 ---（包括带空格的）
        html = re.sub(r'\s*---+\s*', '', html)
        
        # 先处理粗体（在段落化之前）
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html, flags=re.DOTALL)
        
        # 链接
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        # 列表
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n?)+', r'<ul>\g<0></ul>', html, flags=re.DOTALL)
        
        # 段落（不处理已加标签的）
        lines = html.split('\n')
        processed = []
        for line in lines:
            line = line.strip()
        return html

    def _generate_poster_html(self, sections: List[Dict], issue_number: int, 
                              time_range: str, stats: Dict) -> str:
        """生成海报级 HTML"""
        now = datetime.now()
        total_items = stats.get('total_items', 0) if stats else 0
        cv_count = stats.get('cv_count', 0) if stats else 0
        source_count = stats.get('source_count', 0) if stats else 0
        
        content_html = self._render_sections(sections)
