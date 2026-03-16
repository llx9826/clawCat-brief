#!/usr/bin/env python3
"""
AI/CV Weekly - 数据渲染层（Jinja2 模板版 v5）

【特性】
- Jinja2 模板引擎
- 响应式设计
- 自动暗色模式
- 多主题支持（预留）
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 尝试导入 jinja2，如果失败给出友好提示
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("⚠️ Jinja2 未安装，使用降级方案")
    print("   运行: pip install jinja2")


class ReportRenderer:
    """报告渲染器（Jinja2 版）"""
    
    # 章节样式配置（支持多种匹配模式）
    SECTION_STYLES = {
        # 核心结论
        '核心结论': {
            'css_class': 'section-core',
            'bg_class': 'bg-amber-50',
            'gradient': 'from-amber-400 to-orange-500',
            'icon': '💡',
            'match_patterns': ['核心结论', '本周核心结论', '一、核心结论', '一、本周核心结论']
        },
        # 重点事件
        '重点事件': {
            'css_class': 'section-events',
            'bg_class': 'bg-blue-50',
            'gradient': 'from-blue-400 to-indigo-500',
            'icon': '🔥',
            'match_patterns': ['重点事件', '本周重点事件', '二、重点事件', '二、本周重点事件']
        },
        # 开源项目
        '开源项目': {
            'css_class': 'section-projects',
            'bg_class': 'bg-green-50',
            'gradient': 'from-green-400 to-emerald-500',
            'icon': '🚀',
            'match_patterns': ['开源项目', '开源项目推荐', '三、开源项目', '三、开源项目推荐']
        },
        # 论文推荐
        '论文推荐': {
            'css_class': 'section-papers',
            'bg_class': 'bg-cyan-50',
            'gradient': 'from-cyan-400 to-blue-500',
            'icon': '📄',
            'match_patterns': ['论文', '论文推荐', '四、论文', '四、论文推荐']
        },
        # 趋势分析
        '趋势分析': {
            'css_class': 'section-trends',
            'bg_class': 'bg-purple-50',
            'gradient': 'from-purple-400 to-pink-500',
            'icon': '📈',
            'match_patterns': ['趋势', '趋势分析', '本周趋势', '五、趋势', '五、趋势分析', '五、本周趋势']
        },
        # 复盘
        '复盘': {
            'css_class': 'section-review',
            'bg_class': 'bg-orange-50',
            'gradient': 'from-orange-400 to-red-500',
            'icon': '🦞',
            'match_patterns': ['复盘', 'Claw 复盘', '六、复盘', '六、Claw 复盘', '主编复盘']
        },
    }
    
    DEFAULT_STYLE = {
        'css_class': 'section-default',
        'bg_class': 'bg-gray-50',
        'gradient': 'from-gray-400 to-gray-500',
        'icon': '📝',
        'match_patterns': []
    }
    
    def __init__(self, output_dir: Path = None, template_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        
        # 初始化 Jinja2 环境
        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
            self.template = self.env.get_template('weekly.html')
        else:
            self.template = None
    
    def render(self, markdown: str, issue_number: int, time_range: str, 
               stats: Dict = None, theme: str = 'default') -> Dict:
        """
        渲染报告
        
        Args:
            markdown: 周报 Markdown 内容
            issue_number: 期号
            time_range: 时间范围
            stats: 统计数据
            theme: 主题名称（预留）
        
        Returns:
            Dict: 包含 html, html_path, md_path
        """
        if not JINJA2_AVAILABLE:
            raise RuntimeError("Jinja2 未安装，无法渲染模板")
        
        # 解析章节
        sections = self._parse_sections(markdown)
        
        # 准备模板数据
        template_data = {
            'title': f'AI/CV Weekly - 第{issue_number}期',
            'issue_number': issue_number,
            'time_range': time_range,
            'stats': stats or {},
            'sections': sections,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'theme': theme
        }
        
        # 渲染 HTML
        html = self.template.render(**template_data)
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"weekly_{timestamp}.html"
        md_path = self.output_dir / f"weekly_{timestamp}.md"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return {
            "html": html,
            "html_path": str(html_path),
            "md_path": str(md_path)
        }
    
    def _parse_sections(self, markdown: str) -> List[Dict[str, Any]]:
        """解析章节并添加样式信息"""
        sections = []
        lines = markdown.split('\n')
        current_title = None
        content_lines = []
        
        for line in lines:
            if line.startswith('## '):
                # 保存上一个章节
                if current_title:
                    sections.append(self._create_section(current_title, content_lines))
                
                # 开始新章节
                current_title = line[3:].strip()
                current_title = re.sub(r'\*\*', '', current_title)
                current_title = re.sub(r'🦞\s*', '', current_title)
                content_lines = []
            elif line.strip() or content_lines:
                content_lines.append(line)
        
        # 保存最后一个章节
        if current_title:
            sections.append(self._create_section(current_title, content_lines))
        
        return sections
    
    def _match_section_style(self, title: str) -> Dict[str, Any]:
        """根据标题匹配章节样式"""
        # 清理标题（移除序号、空格等）
        clean_title = title.strip()
        
        # 尝试直接匹配
        if clean_title in self.SECTION_STYLES:
            return self.SECTION_STYLES[clean_title]
        
        # 尝试匹配 patterns
        for style_name, style_config in self.SECTION_STYLES.items():
            patterns = style_config.get('match_patterns', [])
            for pattern in patterns:
                if pattern in clean_title or clean_title in pattern:
                    return style_config
        
        # 尝试模糊匹配（包含关键词）
        for style_name, style_config in self.SECTION_STYLES.items():
            if style_name in clean_title:
                return style_config
            patterns = style_config.get('match_patterns', [])
            for pattern in patterns:
                # 提取关键词（去掉序号）
                keyword = pattern.replace('一、', '').replace('二、', '').replace('三、', '').replace('四、', '').replace('五、', '').replace('六、', '')
                if keyword and keyword in clean_title:
                    return style_config
        
        return self.DEFAULT_STYLE

    def _create_section(self, title: str, content_lines: List[str]) -> Dict[str, Any]:
        """创建章节数据"""
        # 获取样式配置（使用新的匹配方法）
        style = self._match_section_style(title)
        
        # 渲染内容 HTML
        content_html = self._render_content('\n'.join(content_lines))
        
        return {
            'title': title,
            'content': content_html,
            **style
        }
    
    def _render_content(self, content: str) -> str:
        """渲染内容为 HTML"""
        # 移除分隔符
        content = re.sub(r'\n+---+\n*', '\n\n', content)
        
        # 按 ### 分割成块
        if '### ' in content:
            blocks = re.split(r'\n+(?=### \d+\.)', content.strip())
            html_parts = []
            for block in blocks:
                if block.strip():
                    html = self._render_block(block.strip())
                    html_parts.append(html)
            return '\n'.join(html_parts)
        else:
            return self._render_block(content.strip())
    
    def _render_block(self, content: str) -> str:
        """渲染单个内容块"""
        lines = content.split('\n')
        html_lines = []
        in_commentary = False
        commentary_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 标题 ### 1. xxx
            if stripped.startswith('### '):
                title = stripped[4:]
                html_lines.append(f'<div class="item-block"><h3>{title}</h3>')
                i += 1
                continue
            
            # 子标题 #### xxx
            if stripped.startswith('#### '):
                title = stripped[5:]
                html_lines.append(f'<h4>{title}</h4>')
                i += 1
                continue
            
            # 锐评开始
            if re.match(r'\*\*🦞 Claw 锐评\*\*[:：]', stripped):
                in_commentary = True
                commentary_lines = []
                match = re.match(r'\*\*🦞 Claw 锐评\*\*[:：](.+)', stripped)
                if match:
                    commentary_lines.append(match.group(1))
                i += 1
                continue
            
            # 锐评内容或结束
            if in_commentary:
                if not stripped or stripped.startswith('### ') or stripped.startswith('#### ') or re.match(r'\*\*🦞', stripped):
                    if commentary_lines:
                        text = ' '.join(commentary_lines)
                        text = self._inline_format(text)
                        html_lines.append(f'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>{text}</p></div>')
                    in_commentary = False
                    commentary_lines = []
                    # 不递增 i，让当前行被正常处理
                    continue
                else:
                    commentary_lines.append(stripped)
                    i += 1
                    continue
            
            # 列表项
            if stripped.startswith('- ') and not stripped.startswith('---'):
                list_items = [stripped[2:]]
                i += 1
                while i < len(lines):
                    next_stripped = lines[i].strip()
                    if next_stripped.startswith('- '):
                        list_items.append(next_stripped[2:])
                        i += 1
                    else:
                        break
                html_lines.append('<ul>')
                for item in list_items:
                    item = self._inline_format(item)
                    html_lines.append(f'<li>{item}</li>')
                html_lines.append('</ul>')
                continue
            
            # 普通段落
            if stripped:
                line = self._inline_format(line)
                html_lines.append(f'<p>{line}</p>')
            
            i += 1
        
        # 关闭最后的锐评
        if in_commentary and commentary_lines:
            text = ' '.join(commentary_lines)
            text = self._inline_format(text)
            html_lines.append(f'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>{text}</p></div>')
        
        # 关闭 item-block
        if html_lines:
            html_lines.append('</div>')
        
        return '\n'.join(html_lines)
    
    def _inline_format(self, text: str) -> str:
        """行内格式化"""
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        return text
