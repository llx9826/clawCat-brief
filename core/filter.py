#!/usr/bin/env python3
"""
AI/CV Weekly - 过滤层（数据预处理）

【职责】
1. 低价值内容剔除
2. CV/OCR 优先排序
3. 领域标签分配
4. 去重

【不做什么】
- 不生成内容（Editor 的事）
- 不渲染格式（Renderer 的事）
- 不缓存数据
"""

from typing import Dict, List


class ItemFilter:
    """过滤器（CV/OCR 优先）"""
    
    def __init__(self):
        # CV/OCR 领域优先级（越高越优先）
        self.cv_keywords = {
            "ocr": 5,
            "document ai": 5,
            "document understanding": 5,
            "layout analysis": 5,
            "computer vision": 4,
            "cv": 4,
            "vision": 3,
            "image": 3,
            "multimodal": 4,
            "vlm": 4,
            "vision-language": 4,
            "detection": 3,
            "segmentation": 3,
            "medical imaging": 3,
            "medical": 2,
        }
        
        # 低价值内容（直接剔除）
        self.low_value = [
            "portfolio", "resume", "personal website",
            "crypto", "nft", "blockchain",
            "awesome list", "tutorial for beginners",
            "job posting", "hiring"
        ]
    
    def filter_and_rank(self, items: List[Dict], max_keep: int = 20) -> List[Dict]:
        """
        过滤和排序
        
        Args:
            items: 原始条目列表
            max_keep: 最大保留数量
        
        Returns:
            精选后的条目列表
        """
        print(f"开始过滤（{len(items)} 条 → 最多{max_keep} 条）...")
        
        # 1. 过滤低价值内容
        before = len(items)
        filtered = [item for item in items if not self._is_low_value(item)]
        print(f"   低价值剔除：{before - len(filtered)} 条")
        
        # 2. 去重（基于标题）
        before = len(filtered)
        filtered = self._deduplicate(filtered)
        print(f"   去重：{before - len(filtered)} 条")
        
        # 3. 评分
        scored = self._score_items(filtered)
        
        # 4. 排序
        scored.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # 5. 选取 Top N
        selected = scored[:max_keep]
        
        # 6. 分配领域标签
        for item in selected:
            item['domain_tags'] = self._assign_tags(item)
        
        # 统计 CV/OCR 相关
        cv_count = sum(1 for i in selected if any(t in i.get('domain_tags', []) for t in ['CV', 'OCR', 'Medical Imaging']))
        print(f"   CV/OCR 相关：{cv_count}/{len(selected)} 条")
        
        return selected
    
    def _is_low_value(self, item: Dict) -> bool:
        """检查是否是低价值内容"""
        text = (
            item.get('title', '') + ' ' +
            item.get('raw_text', '')
        ).lower()
        
        return any(kw in text for kw in self.low_value)
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """去重（基于标题相似度）"""
        seen = set()
        unique = []
        
        for item in items:
            # 标题前 50 字符作为 key
            key = item.get('title', '').lower()[:50]
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique
    
    def _score_items(self, items: List[Dict]) -> List[Dict]:
        """评分"""
        for item in items:
            text = (
                item.get('title', '') + ' ' +
                item.get('raw_text', '')
            ).lower()
            
            # 基础分
            score = 5
            
            # CV/OCR 关键词加分
            for keyword, points in self.cv_keywords.items():
                if keyword in text:
                    score += points
                    break
            
            # 来源质量加分
            source = item.get('source', '')
            if source == 'arxiv':
                score += 2
            elif source == 'github':
                stars = item.get('meta', {}).get('stars', 0)
                if stars >= 1000:
                    score += 3
                elif stars >= 500:
                    score += 2
                elif stars >= 100:
                    score += 1
            elif source in ['jiqizhixin', '36kr']:
                score += 1
            
            # 热度加分
            views = item.get('meta', {}).get('views', 0)
            points = item.get('meta', {}).get('points', 0)
            if views >= 10000 or points >= 100:
                score += 2
            elif views >= 1000 or points >= 50:
                score += 1
            
            item['final_score'] = score
        
        return items
    
    def _assign_tags(self, item: Dict) -> List[str]:
        """分配领域标签"""
        text = (
            item.get('title', '') + ' ' +
            item.get('raw_text', '')
        ).lower()
        
        tags = []
        
        # OCR/文档理解
        if any(kw in text for kw in ['ocr', 'document ai', 'document understanding', 'layout analysis', 'text recognition']):
            tags.append('OCR')
        
        # CV
        if any(kw in text for kw in ['computer vision', 'cv', 'vision', 'image', 'detection', 'segmentation']):
            tags.append('CV')
        
        # 多模态
        if any(kw in text for kw in ['multimodal', 'vlm', 'vision-language', 'text-to-image']):
            tags.append('Multimodal')
        
        # 医疗
        if any(kw in text for kw in ['medical', 'healthcare', 'clinical', 'pathology']):
            tags.append('Medical Imaging')
        
        # 默认标签
        if not tags:
            source = item.get('source', '')
            if source == 'arxiv':
                tags.append('Research')
            elif source == 'github':
                tags.append('Open Source')
            elif source in ['jiqizhixin', '36kr']:
                tags.append('Industry')
            else:
                tags.append('AI')
        
        return tags[:3]
