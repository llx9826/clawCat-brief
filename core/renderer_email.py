#!/usr/bin/env python3
"""
AI/CV Weekly - 邮件专用渲染器（内联样式版）

【特性】
- 内联 CSS 样式（邮件客户端兼容）
- 简化版设计（确保邮件可读性）
- 基于 Jinja2 模板
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class EmailReportRenderer:
    """邮件报告渲染器（内联样式版）"""
    
    SECTION_STYLES = {
        '核心结论': {'color': '#f59e0b', 'icon': '💡', 'bg': '#fffbeb'},
        '重点事件': {'color': '#3b82f6', 'icon': '🔥', 'bg': '#eff6ff'},
        '开源项目': {'color': '#22c55e', 'icon': '🚀', 'bg': '#f0fdf4'},
        '论文推荐': {'color': '#06b6d4', 'icon': '📄', 'bg': '#ecfeff'},
        '趋势分析': {'color': '#a855f7', 'icon': '📈', 'bg': '#faf5ff'},
        '复盘': {'color': '#f97316', 'icon': '🦞', 'bg': '#fff7ed'},
        'Claw 复盘': {'color': '#f97316', 'icon': '🦞', 'bg': '#fff7ed'},
    }
    
    DEFAULT_STYLE = {'color': '#6b7280', 'icon': '📝', 'bg': '#f9fafb'}
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def render(self, markdown: str, issue_number: int, time_range: str, 
               stats: Dict = None) -> str:
        """渲染邮件 HTML"""
        sections = self._parse_sections(markdown)
        
        html = self._generate_html(sections, issue_number, time_range, stats or {})
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"weekly_email_{timestamp}.html"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return html
    
    def _generate_html(self, sections: List[Dict], issue_number: int,
                       time_range: str, stats: Dict) -> str:
        """生成邮件 HTML（内联样式）"""
        total = stats.get('total_items', 0)
        cv = stats.get('cv_count', 0)
        sources = stats.get('source_count', 0)
        
        sections_html = ''
        for section in sections:
            sections_html += self._render_section(section)
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI/CV Weekly - 第{issue_number}期</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f3f4f6; line-height: 1.75;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%); border-radius: 16px; padding: 30px 20px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 10px;">🦞</div>
                            <h1 style="color: #fbbf24; font-size: 28px; font-weight: 800; margin: 0 0 8px;">AI/CV Weekly</h1>
                            <p style="color: #c7d2fe; font-size: 14px; margin: 0;">第 {issue_number} 期 · {time_range}</p>
                            
                            <!-- Stats -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px;">
                                <tr>
                                    <td width="33%" style="text-align: center; padding: 10px;">
                                        <div style="background: rgba(255,255,255,0.15); border-radius: 12px; padding: 15px;">
                                            <div style="color: #fbbf24; font-size: 24px; font-weight: 700;">{total}</div>
                                            <div style="color: #c7d2fe; font-size: 11px; margin-top: 4px;">原始数据</div>
                                        </div>
                                    </td>
                                    <td width="33%" style="text-align: center; padding: 10px;">
                                        <div style="background: rgba(255,255,255,0.15); border-radius: 12px; padding: 15px;">
                                            <div style="color: #86efac; font-size: 24px; font-weight: 700;">{cv}</div>
                                            <div style="color: #c7d2fe; font-size: 11px; margin-top: 4px;">CV/OCR</div>
                                        </div>
                                    </td>
                                    <td width="33%" style="text-align: center; padding: 10px;">
                                        <div style="background: rgba(255,255,255,0.15); border-radius: 12px; padding: 15px;">
                                            <div style="color: #93c5fd; font-size: 24px; font-weight: 700;">{sources}</div>
                                            <div style="color: #c7d2fe; font-size: 11px; margin-top: 4px;">数据源</div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Spacer -->
                    <tr><td height="16"></td></tr>
                    
                    <!-- Sections -->
                    {sections_html}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="text-align: center; padding: 30px; color: #6b7280; font-size: 12px;">
                            <div style="font-size: 32px; margin-bottom: 10px;">🦞</div>
                            <p style="font-weight: 600; color: #374151; margin: 0 0 4px;">AI/CV Weekly</p>
                            <p style="margin: 0;">{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    def _render_section(self, section: Dict) -> str:
        """渲染单个章节（邮件版）"""
        style = self.SECTION_STYLES.get(section['title'], self.DEFAULT_STYLE)
        
        return f'''
                    <tr>
                        <td style="background: {style['bg']}; border-radius: 16px; padding: 20px; border-left: 4px solid {style['color']}; margin-bottom: 16px;">
                            <!-- Section Header -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
                                <tr>
                                    <td style="font-size: 18px; font-weight: 700; color: #1f2937;">
                                        <span style="margin-right: 8px;">{style['icon']}</span>{section['title']}
                                    </td>
                                </tr>
                            </table>
                            <!-- Section Content -->
                            <div style="color: #4b5563; font-size: 15px; line-height: 1.8;">
                                {section['content']}
                            </div>
                        </td>
                    </tr>
                    <tr><td height="16"></td></tr>
        '''
    
    def _parse_sections(self, markdown: str) -> List[Dict[str, Any]]:
        """解析章节"""
        sections = []
        lines = markdown.split('\n')
        current_title = None
        content_lines = []
        
        for line in lines:
            if line.startswith('## '):
                if current_title:
                    sections.append({
                        'title': current_title,
                        'content': self._render_content('\n'.join(content_lines))
                    })
                current_title = line[3:].strip()
                current_title = re.sub(r'\*\*', '', current_title)
                current_title = re.sub(r'🦞\s*', '', current_title)
                content_lines = []
            elif line.strip() or content_lines:
                content_lines.append(line)
        
        if current_title:
            sections.append({
                'title': current_title,
                'content': self._render_content('\n'.join(content_lines))
            })
        
        return sections
    
    def _render_content(self, content: str) -> str:
        """渲染内容为邮件 HTML"""
        lines = content.split('\n')
        html_lines = []
        in_list = False
        list_items = []
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                if in_list:
                    html_lines.append(f'<ul style="margin: 12px 0; padding-left: 20px;">{"".join(list_items)}</ul>')
                    in_list = False
                    list_items = []
                continue
            
            # 三级标题 ### 1. xxx
            if stripped.startswith('### '):
                if in_list:
                    html_lines.append(f'<ul style="margin: 12px 0; padding-left: 20px;">{"".join(list_items)}</ul>')
                    in_list = False
                    list_items = []
                title = stripped[4:]
                title = self._inline_format(title)
                html_lines.append(f'<h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #e5e7eb;">{title}</h3>')
                continue
            
            # 四级标题 #### xxx
            if stripped.startswith('#### '):
                if in_list:
                    html_lines.append(f'<ul style="margin: 12px 0; padding-left: 20px;">{"".join(list_items)}</ul>')
                    in_list = False
                    list_items = []
                title = stripped[5:]
                title = self._inline_format(title)
                html_lines.append(f'<h4 style="font-size: 15px; font-weight: 600; color: #374151; margin: 16px 0 8px;">{title}</h4>')
                continue
            
            # 列表项
            if stripped.startswith('- '):
                if not in_list:
                    in_list = True
                    list_items = []
                item = stripped[2:]
                item = self._inline_format(item)
                list_items.append(f'<li style="margin: 8px 0;">{item}</li>')
                continue
            
            # 关闭列表
            if in_list:
                html_lines.append(f'<ul style="margin: 12px 0; padding-left: 20px;">{"".join(list_items)}</ul>')
                in_list = False
                list_items = []
            
            # 锐评
            if re.match(r'\*\*🦞 Claw 锐评\*\*[:：]', stripped):
                match = re.match(r'\*\*🦞 Claw 锐评\*\*[:：](.+)', stripped)
                if match:
                    text = self._inline_format(match.group(1))
                    html_lines.append(f'<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #fbbf24; border-radius: 12px; padding: 12px; margin: 12px 0;"><div style="font-weight: 700; color: #92400e; font-size: 13px; margin-bottom: 6px;">🦞 Claw 锐评</div><p style="color: #78350f; font-style: italic; margin: 0; font-size: 14px;">{text}</p></div>')
                continue
            
            # 普通段落
            text = self._inline_format(stripped)
            html_lines.append(f'<p style="margin: 12px 0;">{text}</p>')
        
        if in_list:
            html_lines.append(f'<ul style="margin: 12px 0; padding-left: 20px;">{"".join(list_items)}</ul>')
        
        return '\n'.join(html_lines)
    
    def _inline_format(self, text: str) -> str:
        """行内格式化"""
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #111827; font-weight: 600;">\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color: #4f46e5; text-decoration: none; font-weight: 500;">\1</a>', text)
        return text
