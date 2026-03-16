#!/usr/bin/env python3
"""
GitHub 增强抓取模块 - 读取 README 获取详细描述
"""

import base64
from typing import Dict, List


class GitHubEnhancer:
    """GitHub 项目信息增强器"""
    
    @staticmethod
    async def fetch_readme(session, repo_full_name: str, branch: str, headers: Dict) -> str:
        """抓取 GitHub README.md 内容"""
        try:
            # 尝试多个 README 路径
            possible_paths = [
                f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/README.md",
                f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/readme.md",
            ]
            
            for url in possible_paths:
                try:
                    async with session.get(url, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            return GitHubEnhancer.extract_key_points(content)
                except:
                    continue
            
            # 尝试 API 方式
            api_url = f"https://api.github.com/repos/{repo_full_name}/readme"
            try:
                async with session.get(api_url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = base64.b64decode(data.get('content', '')).decode('utf-8')
                        return GitHubEnhancer.extract_key_points(content)
            except:
                pass
            
            return ""
        except Exception as e:
            return ""
    
    @staticmethod
    def extract_key_points(readme: str) -> str:
        """从 README 提取关键信息"""
        lines = readme.split('\n')
        key_sections = []
        
        # 提取标题后的第一段（通常是项目简介）
        in_header = True
        for line in lines:
            line = line.strip()
            if not line:
                in_header = False
                continue
            if in_header and line.startswith('#'):
                continue
            if not in_header and line and not line.startswith('```'):
                key_sections.append(line)
                if len(key_sections) >= 5:
                    break
        
        # 查找 Features/Usage/Installation 等关键部分
        important_keywords = ['feature', '特性', '功能', 'usage', '使用', 'install', '安装', 'what is', 'introduction', '介绍']
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in important_keywords):
                # 提取该部分接下来的 3 行
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('```') and not lines[j].startswith('#'):
                        key_sections.append(lines[j].strip())
        
        result = ' '.join(key_sections)
        return result[:2000]  # 增加长度从 1200 到 2000
    
    @staticmethod
    def merge_description(short_desc: str, readme_text: str, topics: List[str]) -> str:
        """合并 GitHub 描述和 README 信息"""
        parts = []
        
        # README 关键信息（优先）
        if readme_text:
            parts.append(f"{readme_text}")
        
        # 简短描述（补充）
        if short_desc and short_desc != '无描述' and short_desc not in readme_text:
            parts.append(f"简介：{short_desc}")
        
        # 技术标签
        if topics:
            parts.append(f"技术栈：{', '.join(topics[:5])}")
        
        return ' | '.join(parts)
