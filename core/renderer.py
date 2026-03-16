#!/usr/bin/env python3
"""
AI/CV Weekly - 数据渲染层（响应式版 v4）

【特性】
- 移动优先设计
- 三级响应式断点
- 自动暗色模式
- 玻璃态视觉效果
- 触摸友好交互
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class ReportRenderer:
    """报告渲染器（响应式版）"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def render(self, markdown: str, issue_number: int, time_range: str, 
               stats: Dict = None) -> Dict:
        """渲染报告"""
        sections = self._parse_sections(markdown)
        html = self._generate_html(sections, issue_number, time_range, stats)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"weekly_{timestamp}.html"
        md_path = self.output_dir / f"weekly_{timestamp}.md"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return {"html": html, "html_path": str(html_path), "md_path": str(md_path)}
    
    def _parse_sections(self, markdown: str) -> List[Dict]:
        """解析章节"""
        sections = []
        lines = markdown.split('\n')
        current = None
        content = []
        
        for line in lines:
            if line.startswith('## '):
                if current:
                    sections.append({'title': current, 'content': '\n'.join(content)})
                title = line[3:].strip()
                title = re.sub(r'\*\*', '', title)
                title = re.sub(r'🦞\s*', '', title)
                current = title.strip()
                content = []
            elif line.strip() or content:
                content.append(line)
        
        if current:
            sections.append({'title': current, 'content': '\n'.join(content)})
        
        return sections
    
    def _get_section_style(self, title: str) -> Dict:
        """获取章节样式"""
        styles = {
            '核心结论': {'gradient': 'from-amber-400 to-orange-500', 'icon': '💡', 'bg': 'bg-amber-50'},
            '重点事件': {'gradient': 'from-blue-400 to-indigo-500', 'icon': '🔥', 'bg': 'bg-blue-50'},
            '开源项目': {'gradient': 'from-green-400 to-emerald-500', 'icon': '🚀', 'bg': 'bg-green-50'},
            '论文推荐': {'gradient': 'from-cyan-400 to-blue-500', 'icon': '📄', 'bg': 'bg-cyan-50'},
            '趋势分析': {'gradient': 'from-purple-400 to-pink-500', 'icon': '📈', 'bg': 'bg-purple-50'},
            '复盘': {'gradient': 'from-orange-400 to-red-500', 'icon': '🦞', 'bg': 'bg-orange-50'},
            'Claw 复盘': {'gradient': 'from-orange-400 to-red-500', 'icon': '🦞', 'bg': 'bg-orange-50'},
        }
        
        for key, style in styles.items():
            if key in title:
                return style
        
        return {'gradient': 'from-gray-400 to-gray-500', 'icon': '📝', 'bg': 'bg-gray-50'}
    
    def _generate_html(self, sections: List[Dict], issue_number: int,
                       time_range: str, stats: Dict) -> str:
        """生成响应式 HTML"""
        now = datetime.now()
        total = stats.get('total_items', 0) if stats else 0
        cv = stats.get('cv_count', 0) if stats else 0
        sources = stats.get('source_count', 0) if stats else 0
        
        sections_html = ''
        for section in sections:
            style = self._get_section_style(section['title'])
            content = self._render_content(section['content'], section['title'])
            
            sections_html += f'''
            <section class="section-card {style['bg']} dark:bg-gray-800/50">
                <div class="section-header">
                    <div class="section-icon-wrapper bg-gradient-to-br {style['gradient']}">
                        <span class="section-icon">{style['icon']}</span>
                    </div>
                    <h2 class="section-title">{section['title']}</h2>
                </div>
                <div class="section-content">
                    {content}
                </div>
            </section>
            '''
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#6366f1">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>AI/CV Weekly - 第{issue_number}期</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        primary: {{
                            50: '#eef2ff',
                            100: '#e0e7ff',
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca',
                        }}
                    }},
                    fontFamily: {{
                        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
                    }},
                }}
            }}
        }}
    </script>
    <style>
        /* ===== 基础样式 ===== */
        * {{
            -webkit-tap-highlight-color: transparent;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.75;
        }}
        
        /* ===== 动态背景 ===== */
        .animated-bg {{
            background: 
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(ellipse 60% 40% at 80% 50%, rgba(236, 72, 153, 0.08), transparent),
                radial-gradient(ellipse 60% 40% at 20% 80%, rgba(20, 184, 166, 0.08), transparent),
                linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
            min-height: 100vh;
        }}
        
        .dark .animated-bg {{
            background: 
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.2), transparent),
                radial-gradient(ellipse 60% 40% at 80% 50%, rgba(236, 72, 153, 0.1), transparent),
                radial-gradient(ellipse 60% 40% at 20% 80%, rgba(20, 184, 166, 0.1), transparent),
                linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        }}
        
        /* ===== 玻璃态卡片 ===== */
        .glass-card {{
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -2px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }}
        
        .dark .glass-card {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.3),
                0 2px 4px -2px rgba(0, 0, 0, 0.3);
        }}
        
        /* ===== 头部样式 ===== */
        .header-gradient {{
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
            position: relative;
            overflow: hidden;
        }}
        
        .header-gradient::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.4) 0%, transparent 50%),
                radial-gradient(circle at 80% 50%, rgba(236, 72, 153, 0.3) 0%, transparent 50%);
            pointer-events: none;
        }}
        
        /* ===== 统计卡片 ===== */
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }}
        
        /* ===== 章节卡片 ===== */
        .section-card {{
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid;
            transition: all 0.3s ease;
        }}
        
        .section-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15);
        }}
        
        .dark .section-card {{
            border-left-color: rgba(255, 255, 255, 0.2);
        }}
        
        /* 各章节边框色 */
        .section-card.bg-amber-50 {{ border-left-color: #f59e0b; }}
        .section-card.bg-blue-50 {{ border-left-color: #3b82f6; }}
        .section-card.bg-green-50 {{ border-left-color: #22c55e; }}
        .section-card.bg-cyan-50 {{ border-left-color: #06b6d4; }}
        .section-card.bg-purple-50 {{ border-left-color: #a855f7; }}
        .section-card.bg-orange-50 {{ border-left-color: #f97316; }}
        .section-card.bg-gray-50 {{ border-left-color: #6b7280; }}
        
        .dark .section-card.bg-amber-50 {{ border-left-color: #fbbf24; }}
        .dark .section-card.bg-blue-50 {{ border-left-color: #60a5fa; }}
        .dark .section-card.bg-green-50 {{ border-left-color: #4ade80; }}
        .dark .section-card.bg-cyan-50 {{ border-left-color: #22d3ee; }}
        .dark .section-card.bg-purple-50 {{ border-left-color: #c084fc; }}
        .dark .section-card.bg-orange-50 {{ border-left-color: #fb923c; }}
        .dark .section-card.bg-gray-50 {{ border-left-color: #9ca3af; }}
        
        /* ===== 章节头部 ===== */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        }}
        
        .dark .section-header {{
            border-bottom-color: rgba(255, 255, 255, 0.1);
        }}
        
        .section-icon-wrapper {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .section-icon {{
            font-size: 22px;
            filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));
        }}
        
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #1f2937;
            margin: 0;
            line-height: 1.3;
        }}
        
        .dark .section-title {{
            color: #f3f4f6;
        }}
        
        /* ===== 内容样式 ===== */
        .section-content {{
            color: #4b5563;
            font-size: 15px;
            line-height: 1.8;
        }}
        
        .dark .section-content {{
            color: #d1d5db;
        }}
        
        .section-content h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #111827;
            margin: 20px 0 10px;
            padding-bottom: 6px;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .dark .section-content h3 {{
            color: #f9fafb;
            border-bottom-color: #374151;
        }}
        
        .section-content h4 {{
            font-size: 15px;
            font-weight: 600;
            color: #374151;
            margin: 16px 0 8px;
        }}
        
        .dark .section-content h4 {{
            color: #e5e7eb;
        }}
        
        .section-content p {{
            margin: 12px 0;
        }}
        
        .section-content ul {{
            margin: 12px 0;
            padding-left: 20px;
        }}
        
        .section-content li {{
            margin: 8px 0;
        }}
        
        .section-content strong {{
            color: #111827;
            font-weight: 600;
        }}
        
        .dark .section-content strong {{
            color: #f9fafb;
        }}
        
        .section-content a {{
            color: #4f46e5;
            text-decoration: none;
            font-weight: 500;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
        }}
        
        .dark .section-content a {{
            color: #818cf8;
        }}
        
        .section-content a:hover {{
            border-bottom-color: currentColor;
        }}
        
        /* ===== 项目块 ===== */
        .item-block {{
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }}
        
        .dark .item-block {{
            border-bottom-color: rgba(255, 255, 255, 0.08);
        }}
        
        .item-block:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        /* ===== Claw 锐评卡片 ===== */
        .claw-commentary {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 2px solid #fbbf24;
            border-radius: 16px;
            padding: 16px;
            margin: 16px 0;
            position: relative;
            box-shadow: 0 4px 12px rgba(251, 191, 36, 0.2);
        }}
        
        .dark .claw-commentary {{
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.1) 100%);
            border-color: rgba(251, 191, 36, 0.5);
        }}
        
        .claw-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            color: #92400e;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        
        .dark .claw-header {{
            color: #fbbf24;
        }}
        
        .claw-header::before {{
            content: "🦞";
            font-size: 16px;
        }}
        
        .claw-commentary p {{
            color: #78350f;
            font-style: italic;
            margin: 0;
            line-height: 1.7;
        }}
        
        .dark .claw-commentary p {{
            color: #fde68a;
        }}
        
        /* ===== 主题切换按钮 ===== */
        .theme-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
            z-index: 100;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}
        
        .theme-toggle:active {{
            transform: scale(0.95);
        }}
        
        /* ===== 响应式断点 ===== */
        
        /* 小屏手机优化 */
        @media (max-width: 374px) {{
            .container {{
                padding: 12px;
            }}
            
            .section-card {{
                padding: 16px;
                border-radius: 16px;
            }}
            
            .section-icon-wrapper {{
                width: 36px;
                height: 36px;
            }}
            
            .section-icon {{
                font-size: 18px;
            }}
            
            .section-title {{
                font-size: 16px;
            }}
            
            .section-content {{
                font-size: 14px;
            }}
            
            .stat-card {{
                padding: 12px 8px;
            }}
            
            .stat-number {{
                font-size: 20px;
            }}
            
            .stat-label {{
                font-size: 10px;
            }}
        }}
        
        /* 平板优化 */
        @media (min-width: 768px) {{
            .container {{
                max-width: 720px;
            }}
            
            .section-card {{
                padding: 28px;
                margin-bottom: 24px;
            }}
            
            .section-title {{
                font-size: 20px;
            }}
            
            .section-content {{
                font-size: 16px;
            }}
            
            .section-icon-wrapper {{
                width: 48px;
                height: 48px;
            }}
            
            .section-icon {{
                font-size: 24px;
            }}
            
            .dashboard {{
                gap: 16px;
            }}
            
            .stat-card {{
                padding: 20px;
            }}
        }}
        
        /* 桌面端优化 */
        @media (min-width: 1024px) {{
            .container {{
                max-width: 800px;
                padding: 40px 32px;
            }}
            
            .section-card {{
                padding: 32px;
                border-radius: 24px;
            }}
            
            .section-title {{
                font-size: 22px;
            }}
            
            .claw-commentary {{
                padding: 20px;
            }}
        }}
        
        /* ===== 动画 ===== */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .section-card {{
            animation: fadeInUp 0.5s ease forwards;
        }}
        
        .section-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .section-card:nth-child(2) {{ animation-delay: 0.15s; }}
        .section-card:nth-child(3) {{ animation-delay: 0.2s; }}
        .section-card:nth-child(4) {{ animation-delay: 0.25s; }}
        .section-card:nth-child(5) {{ animation-delay: 0.3s; }}
        .section-card:nth-child(6) {{ animation-delay: 0.35s; }}
        
        /* ===== 打印样式 ===== */
        @media print {{
            .theme-toggle {{
                display: none;
            }}
            
            .animated-bg {{
                background: white !important;
            }}
            
            .section-card {{
                box-shadow: none;
                border: 1px solid #e5e7eb;
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body class="animated-bg">
    <div class="container mx-auto px-4 py-6 md:py-8">
        <!-- Header -->
        <header class="header-gradient rounded-3xl p-6 md:p-10 mb-6 text-white relative overflow-hidden">
            <div class="relative z-10 text-center">
                <div class="text-5xl md:text-6xl mb-3 animate-pulse">🦞</div>
                <h1 class="text-2xl md:text-4xl font-extrabold mb-2 bg-gradient-to-r from-amber-300 via-yellow-300 to-amber-400 bg-clip-text text-transparent">
                    AI/CV Weekly
                </h1>
                <p class="text-sm md:text-base text-gray-300">第 {issue_number} 期 · {time_range}</p>
                
                <!-- Stats Dashboard -->
                <div class="grid grid-cols-3 gap-3 md:gap-4 mt-6">
                    <div class="stat-card rounded-xl p-3 md:p-4">
                        <div class="text-xl md:text-3xl font-bold text-amber-300">{total}</div>
                        <div class="text-xs text-gray-400 mt-1">原始数据</div>
                    </div>
                    <div class="stat-card rounded-xl p-3 md:p-4">
                        <div class="text-xl md:text-3xl font-bold text-green-300">{cv}</div>
                        <div class="text-xs text-gray-400 mt-1">CV/OCR</div>
                    </div>
                    <div class="stat-card rounded-xl p-3 md:p-4">
                        <div class="text-xl md:text-3xl font-bold text-blue-300">{sources}</div>
                        <div class="text-xs text-gray-400 mt-1">数据源</div>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- Sections -->
        <main>
            {sections_html}
        </main>
        
        <!-- Footer -->
        <footer class="text-center py-8 md:py-12 text-gray-500 dark:text-gray-400">
            <div class="text-4xl mb-3">🦞</div>
            <p class="font-semibold text-gray-700 dark:text-gray-300 mb-1">AI/CV Weekly</p>
            <p class="text-xs">{now.strftime("%Y-%m-%d %H:%M")}</p>
        </footer>
    </div>
    
    <!-- Theme Toggle -->
    <button class="theme-toggle" onclick="toggleTheme()" title="切换主题">
        <span id="theme-icon">🌙</span>
    </button>
    
    <script>
        // 主题切换
        function toggleTheme() {{
            const html = document.documentElement;
            const icon = document.getElementById('theme-icon');
            
            if (html.classList.contains('dark')) {{
                html.classList.remove('dark');
                icon.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            }} else {{
                html.classList.add('dark');
                icon.textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            }}
        }}
        
        // 初始化主题
        function initTheme() {{
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const icon = document.getElementById('theme-icon');
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {{
                document.documentElement.classList.add('dark');
                icon.textContent = '☀️';
            }}
        }}
        
        // 页面加载时初始化
        initTheme();
        
        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {{
            if (!localStorage.getItem('theme')) {{
                const icon = document.getElementById('theme-icon');
                if (e.matches) {{
                    document.documentElement.classList.add('dark');
                    icon.textContent = '☀️';
                }} else {{
                    document.documentElement.classList.remove('dark');
                    icon.textContent = '🌙';
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    def _render_content(self, content: str, section_title: str) -> str:
        """渲染内容"""
        content = re.sub(r'\n+---+
*', '

', content)
        
        if '### ' in content:
            blocks = re.split(r'\n+(?=### \d+\.)', content.strip())
            html_parts = []
            for block in blocks:
                if block.strip():
                    html = self._render_block(block.strip())
                    html_parts.append(html)
            return '
'.join(html_parts)
        else:
            return self._render_block(content.strip())
    
    def _render_block(self, content: str) -> str:
        """渲染单个块"""
        lines = content.split('\n')
        html_lines = []
        in_commentary = False
        commentary_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            if stripped.startswith('### '):
                title = stripped[4:]
                html_lines.append(f'<div class="item-block"><h3>{title}</h3>')
                i += 1
                continue
            
            if stripped.startswith('#### '):
                title = stripped[5:]
                html_lines.append(f'<h4>{title}</h4>')
                i += 1
                continue
            
            if re.match(r'\*\*🦞 Claw 锐评\*\*[:：]', stripped):
                in_commentary = True
                commentary_lines = []
                match = re.match(r'\*\*🦞 Claw 锐评\*\*[:：](.+)', stripped)
                if match:
                    commentary_lines.append(match.group(1))
                i += 1
                continue
            
            if in_commentary:
                if not stripped or stripped.startswith('### ') or stripped.startswith('#### ') or re.match(r'\*\*🦞', stripped):
                    if commentary_lines:
                        text = ' '.join(commentary_lines)
                        text = self._inline_format(text)
                        html_lines.append(f'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>{text}</p></div>')
                    in_commentary = False
                    commentary_lines = []
                    continue
                else:
                    commentary_lines.append(stripped)
                    i += 1
                    continue
            
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
            
            if stripped:
                line = self._inline_format(line)
                html_lines.append(f'<p>{line}</p>')
            
            i += 1
        
        if in_commentary and commentary_lines:
            text = ' '.join(commentary_lines)
            text = self._inline_format(text)
            html_lines.append(f'<div class="claw-commentary"><div class="claw-header">Claw 锐评</div><p>{text}</p></div>')
        
        if html_lines:
            html_lines.append('</div>')
        
        return '\n'.join(html_lines)
    
    def _inline_format(self, text: str) -> str:
        """行内格式化"""
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        return text
