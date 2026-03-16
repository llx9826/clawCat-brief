#!/usr/bin/env python3
"""
AI/CV Weekly - Layer 1: 数据提取层（清理版）

【数据源】
- 机器之心、36氪（国内 AI 媒体）
- GitHub（开源项目）
- arXiv、Papers with Code（学术论文）
- Hacker News（技术社区）
- Reddit、Dev.to（海外社区）
- 知乎、掘金（中文社区）
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))
from github_enhancer import GitHubEnhancer


class DataFetcher:
    """数据提取器（清理版）"""
    
    def __init__(self, timeout: int = 30, proxy: str = None, github_token: str = None, time_window_days: int = 7):
        self.timeout = timeout
        self.proxy = proxy
        self.github_token = github_token
        self.time_window_days = time_window_days
        self.cutoff_date = datetime.now() - timedelta(days=time_window_days)
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def _is_within_time_window(self, date_str: str) -> bool:
        """检查日期是否在时间窗口内"""
        if not date_str:
            return True  # 没有时间戳的默认包含
        try:
            # 尝试多种日期格式
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt >= self.cutoff_date
        except:
            return True  # 解析失败默认包含
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout, headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_all(self, params: Dict) -> Dict:
        """从所有数据源抓取（带重试）"""
        print("开始抓取数据源...")
        
        all_items = []
        sources_used = []
        failed_sources = []
        
        # 数据源配置（精简版 - 只保留稳定可靠的源）
        sources_config = [
            # === 核心数据源（高优先级）===
            ("GitHub", self._fetch_github),
            ("arXiv", self._fetch_arxiv),
            ("Hacker News", self._fetch_hackernews),
        ]
        
        # 并行抓取（带并发限制）
        semaphore = asyncio.Semaphore(10)  # 最多10个并发
        
        async def fetch_with_limit(source_name, fetch_func):
            async with semaphore:
                try:
                    for attempt in range(3):
                        try:
                            result = await fetch_func()
                            if result and len(result) > 0:
                                return source_name, result, None
                            else:
                                if attempt == 2:
                                    return source_name, [], "无数据"
                                break
                        except asyncio.TimeoutError:
                            if attempt == 2:
                                return source_name, [], "超时"
                            await asyncio.sleep(1)
                        except Exception as e:
                            if attempt == 2:
                                return source_name, [], str(e)[:50]
                            await asyncio.sleep(1)
                    return source_name, [], "无数据"
                except Exception as e:
                    return source_name, [], str(e)[:50]
        
        # 创建所有任务并并行执行
        tasks = [fetch_with_limit(name, func) for name, func in sources_config]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for result in results:
            if isinstance(result, Exception):
                failed_sources.append(f"未知源({str(result)[:30]})")
                continue
            
            source_name, items, error = result
            if items:
                all_items.extend(items)
                sources_used.append(source_name)
                print(f"✅ {source_name}: {len(items)} 条")
            elif error:
                failed_sources.append(source_name)
                if error != "无数据":
                    print(f"❌ {source_name}: {error}")
        
        print(f"\n总计：{len(all_items)} 条内容，来自 {len(sources_used)} 个数据源")
        if failed_sources:
            print(f"失败源：{', '.join(failed_sources)}")
        
        return {
            "items": all_items,
            "total_count": len(all_items),
            "sources_used": sources_used,
            "failed_sources": failed_sources,
            "fetch_time": datetime.now().isoformat()
        }
    
    async def _fetch_jiqizhixin(self) -> List[Dict]:
        """抓取机器之心（使用 Web Search）"""
        items = []
        try:
            import subprocess
            import json
            import re
            
            result = subprocess.run(
                ['miaoda-studio-cli', 'search-summary', 
                 '--query', '机器之心 人工智能 AI 计算机视觉 最新文章',
                 '--instruction', '提取文章标题、URL、发布时间、摘要，只保留最近7天的文章',
                 '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                search_data = json.loads(result.stdout)
                summary = search_data.get('data', {}).get('summary', '')
                
                # 解析 Markdown 格式的结果
                pattern = r'#### 【\d+】\s*\n- \*\*标题\*\*：([^\n]+)\n- \*\*URL\*\*：([^\n]+)\n- \*\*发布时间\*\*：([^\n]*)'
                matches = re.findall(pattern, summary)
                
                for title, url, date in matches:
                    if 'jiqizhixin.com' in url and self._is_ai_cv_related(title, ''):
                        items.append({
                            "title": title.strip(),
                            "source": "jiqizhixin",
                            "source_name": "机器之心",
                            "url": url.strip(),
                            "raw_text": "",
                            "published_at": date.strip() if date else "",
                            "meta": {
                                "source_type": "web_search",
                                "fetched_via": "miaoda-web-search"
                            }
                        })
                
                print(f"✅ 机器之心(Web Search): {len(items)} 条")
        except Exception as e:
            print(f"机器之心 Web Search 异常：{e}")
        return items
    
    async def _fetch_36kr(self) -> List[Dict]:
        """抓取 36 氪"""
        items = []
        try:
            proxy = self.proxy
            async with self.session.get(
                "https://36kr.com/api/news/list?keyword=AI%20CV%20OCR&per_page=30",
                proxy=proxy,
                allow_redirects=True
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('data', {}).get('items', []):
                        title = article.get('title', '')
                        content = article.get('summary', '')
                        if self._is_ai_cv_related(title, content):
                            items.append({
                                "title": title,
                                "source": "36kr",
                                "source_name": "36 氪",
                                "url": f"https://36kr.com/p/{article.get('id', '')}",
                                "raw_text": content,
                                "published_at": article.get('published_at', ''),
                                "meta": {
                                    "author": article.get('author', {}).get('name', '')
                                }
                            })
        except Exception as e:
            print(f"36 氪抓取异常：{e}")
        return items
    
    async def _fetch_github(self) -> List[Dict]:
        """抓取 GitHub 热门 CV/OCR 项目（不限制时间，避免重复）"""
        items = []
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            seen_repos = set()
            
            # 搜索高热度 CV/OCR 项目（按 Star 排序，不限制时间）
            queries = [
                "computer vision",
                "OCR",
                "multimodal AI",
                "document AI",
                "image segmentation",
                "object detection",
                "PaddleOCR",
                "MMDetection",
                "Transformers vision",
                "OpenCV",
                "vision transformer",
                "layout analysis",
                "text recognition",
                "document understanding",
                "scene text",
            ]
            
            for query in queries:
                try:
                    async with self.session.get(
                        f"https://api.github.com/search/repositories?q={query}+language:python&sort=stars&order=desc&per_page=8",
                        headers=headers,
                        timeout=15
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for repo in data.get('items', []):
                                repo_name = repo['full_name']
                                if repo_name in seen_repos:
                                    continue
                                seen_repos.add(repo_name)
                                
                                stars = repo.get('stargazers_count', 0)
                                desc = repo.get('description', '') or ''
                                
                                # 只保留 AI/CV 相关的
                                if self._is_ai_cv_related(repo_name, desc) and stars >= 50:
                                    items.append({
                                        "title": f"⭐ {repo['full_name']}",
                                        "source": "github",
                                        "source_name": "GitHub",
                                        "url": repo['html_url'],
                                        "raw_text": desc[:500],
                                        "published_at": repo.get('updated_at', ''),
                                        "meta": {
                                            "stars": stars,
                                            "forks": repo.get('forks_count', 0),
                                            "language": repo.get('language', ''),
                                            "topics": repo.get('topics', [])
                                        }
                                    })
                except Exception as e:
                    continue
            
            # 额外：获取本周热门（按最近更新排序）
            try:
                async with self.session.get(
                    "https://api.github.com/search/repositories?q=computer+vision+OR+OCR+OR+multimodal+pushed:>2024-01-01&sort=updated&order=desc&per_page=20",
                    headers=headers,
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get('items', []):
                            repo_name = repo['full_name']
                            if repo_name in seen_repos:
                                continue
                            seen_repos.add(repo_name)
                            
                            stars = repo.get('stargazers_count', 0)
                            desc = repo.get('description', '') or ''
                            
                            if self._is_ai_cv_related(repo_name, desc):
                                items.append({
                                    "title": f"🔥 {repo['full_name']}",
                                    "source": "github",
                                    "source_name": "GitHub Trending",
                                    "url": repo['html_url'],
                                    "raw_text": desc[:500],
                                    "published_at": repo.get('updated_at', ''),
                                    "meta": {
                                        "stars": stars,
                                        "forks": repo.get('forks_count', 0),
                                        "language": repo.get('language', ''),
                                        "topics": repo.get('topics', []),
                                        "recently_updated": True
                                    }
                                })
            except Exception as e:
                pass
                    
            print(f"✅ GitHub: 获取 {len(items)} 条（去重后）")
        except Exception as e:
            print(f"GitHub 抓取异常：{e}")
        return items
    
    async def _fetch_arxiv(self) -> List[Dict]:
        """抓取 arXiv"""
        items = []
        try:
            queries = [
                "search_query=cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results=15",
                "search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=10",
            ]
            for query in queries:
                url = f"http://export.arxiv.org/api/query?{query}"
                async with self.session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        xml_content = await resp.text()
                        parsed = self._parse_arxiv_xml(xml_content)
                        items.extend(parsed)
        except asyncio.TimeoutError:
            print("arXiv 超时")
        except Exception as e:
            print(f"arXiv 异常: {str(e)[:50]}")
        return items
    
    async def _fetch_hackernews(self) -> List[Dict]:
        """抓取 Hacker News"""
        items = []
        try:
            queries = [
                "computer vision OR OCR OR multimodal OR vision model",
                "AI image detection segmentation",
            ]
            for query in queries:
                async with self.session.get(
                    f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&numericFilters=points>5",
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for story in data.get('hits', [])[:5]:
                            items.append({
                                "title": story.get('title', ''),
                                "source": "hackernews",
                                "source_name": "Hacker News",
                                "url": story.get('url', f"https://news.ycombinator.com/item?id={story.get('objectID', '')}"),
                                "raw_text": "",
                                "published_at": story.get('created_at', ''),
                                "meta": {
                                    "points": story.get('points', 0),
                                    "comments": story.get('num_comments', 0)
                                }
                            })
        except Exception as e:
            print(f"Hacker News 抓取异常：{e}")
        return items
    
    async def _fetch_paperswithcode(self) -> List[Dict]:
        """抓取 Papers with Code"""
        items = []
        try:
            async with self.session.get(
                "https://paperswithcode.com/api/v1/papers/?ordering=-date&page=1&items_per_page=20",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for paper in data.get('results', []):
                        title = paper.get('title', '')
                        if self._is_ai_cv_related(title, paper.get('abstract', '')):
                            items.append({
                                "title": title,
                                "source": "paperswithcode",
                                "source_name": "Papers with Code",
                                "url": paper.get('url', ''),
                                "raw_text": paper.get('abstract', ''),
                                "published_at": paper.get('date', ''),
                                "meta": {
                                    "github_stars": paper.get('github_stars', 0),
                                    "tasks": [t.get('name') for t in paper.get('tasks', [])]
                                }
                            })
        except Exception as e:
            print(f"Papers with Code 抓取异常：{e}")
        return items
    
    async def _fetch_reddit(self) -> List[Dict]:
        """抓取 Reddit（使用 RedditSearch 和 RSSHub）"""
        items = []
        try:
            # 方法1: 使用 RedditSearch 网站（无需登录）
            queries = [
                "computer vision",
                "OCR technology",
                "multimodal AI",
                "document AI"
            ]
            
            for query in queries:
                try:
                    await asyncio.sleep(0.5)  # 限速
                    async with self.session.get(
                        f"https://www.reddit.com/search/?q={query.replace(' ', '%20')}&sort=new&t=week&type=posts",
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                        timeout=10
                    ) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            import re
                            # 解析搜索结果
                            pattern = r'<a[^>]*href="(/r/[^/]+/comments/[^/]+/[^/]+)"[^>]*>(.*?)</a>'
                            matches = re.findall(pattern, html)
                            for url, title_html in matches[:5]:
                                title = re.sub(r'<[^>]+>', '', title_html).strip()
                                if title and self._is_ai_cv_related(title, ''):
                                    items.append({
                                        "title": title,
                                        "source": "reddit",
                                        "source_name": "Reddit",
                                        "url": f"https://www.reddit.com{url}",
                                        "raw_text": "",
                                        "published_at": "",
                                        "meta": {"query": query}
                                    })
                except Exception as e:
                    continue
            
            # 方法2: 直接访问热门 subreddit
            subreddits = ['MachineLearning', 'computervision', 'artificial']
            for subreddit in subreddits:
                try:
                    await asyncio.sleep(0.5)
                    async with self.session.get(
                        f"https://www.reddit.com/r/{subreddit}/top/?t=week",
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
                        timeout=10
                    ) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            import re
                            pattern = r'<a[^>]*href="(/r/[^/]+/comments/[^/]+/[^"]+)"[^>]*>(.*?)</a>'
                            matches = re.findall(pattern, html)
                            for url, title_html in matches[:5]:
                                title = re.sub(r'<[^>]+>', '', title_html).strip()
                                if title and len(title) > 10 and self._is_ai_cv_related(title, ''):
                                    items.append({
                                        "title": title,
                                        "source": "reddit",
                                        "source_name": f"Reddit r/{subreddit}",
                                        "url": f"https://www.reddit.com{url}",
                                        "raw_text": "",
                                        "published_at": "",
                                        "meta": {}
                                    })
                except Exception as e:
                    continue
            
            # 去重
            seen = set()
            unique_items = []
            for item in items:
                key = item['title'][:50]
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            
            print(f"✅ Reddit: {len(unique_items)} 条")
            return unique_items
            
        except Exception as e:
            print(f"Reddit 抓取异常：{e}")
        return items
    
    async def _fetch_devto(self) -> List[Dict]:
        """抓取 Dev.to"""
        items = []
        try:
            async with self.session.get(
                "https://dev.to/api/articles?tag=ai&tag=machinelearning&per_page=10",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data:
                        title = article.get('title', '')
                        if self._is_ai_cv_related(title, article.get('description', '')):
                            items.append({
                                "title": title,
                                "source": "devto",
                                "source_name": "Dev.to",
                                "url": article.get('url', ''),
                                "raw_text": article.get('description', ''),
                                "published_at": article.get('published_at', ''),
                                "meta": {
                                    "reactions": article.get('public_reactions_count', 0),
                                    "comments": article.get('comments_count', 0)
                                }
                            })
        except Exception as e:
            print(f"Dev.to 抓取异常：{e}")
        return items
    
    async def _fetch_zhihu(self) -> List[Dict]:
        """抓取知乎"""
        items = []
        try:
            proxy = self.proxy
            async with self.session.get(
                "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20",
                proxy=proxy,
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get('data', []):
                        title = item.get('target', {}).get('title', '')
                        if self._is_ai_cv_related(title, ''):
                            items.append({
                                "title": title,
                                "source": "zhihu",
                                "source_name": "知乎",
                                "url": item.get('target', {}).get('url', ''),
                                "raw_text": item.get('target', {}).get('excerpt', ''),
                                "published_at": '',
                                "meta": {
                                    "heat": item.get('detail_text', '')
                                }
                            })
        except Exception as e:
            print(f"知乎抓取异常：{e}")
        return items
    
    async def _fetch_juejin(self) -> List[Dict]:
        """抓取掘金"""
        items = []
        try:
            async with self.session.get(
                "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed",
                json={"client_type": 2608, "cursor": "0", "id_type": 2, "limit": 20}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get('data', []):
                        article = item.get('item_info', {}).get('article_info', {})
                        title = article.get('title', '')
                        if self._is_ai_cv_related(title, article.get('brief_content', '')):
                            items.append({
                                "title": title,
                                "source": "juejin",
                                "source_name": "掘金",
                                "url": f"https://juejin.cn/post/{article.get('article_id', '')}",
                                "raw_text": article.get('brief_content', ''),
                                "published_at": '',
                                "meta": {
                                    "views": article.get('view_count', 0),
                                    "likes": article.get('digg_count', 0)
                                }
                            })
        except Exception as e:
            print(f"掘金抓取异常：{e}")
        return items
    
    # ==================== 新增数据源 ====================
    
    async def _fetch_csdn(self) -> List[Dict]:
        """抓取 CSDN"""
        items = []
        try:
            async with self.session.get(
                "https://www.csdn.net/api/articles?type=more&category=ai",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('articles', []):
                        title = article.get('title', '')
                        if self._is_ai_cv_related(title, article.get('desc', '')):
                            items.append({
                                "title": title,
                                "source": "csdn",
                                "source_name": "CSDN",
                                "url": article.get('url', ''),
                                "raw_text": article.get('desc', ''),
                                "published_at": article.get('created_at', ''),
                                "meta": {
                                    "views": article.get('views', 0),
                                    "author": article.get('user_name', '')
                                }
                            })
        except Exception as e:
            print(f"CSDN 抓取异常：{e}")
        return items
    
    async def _fetch_infoq_cn(self) -> List[Dict]:
        """抓取 InfoQ 中文"""
        items = []
        try:
            async with self.session.get(
                "https://www.infoq.cn/public/v1/article/getList",
                headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
                json={"size": 20, "type": 1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('data', []):
                        title = article.get('article_title', '')
                        if self._is_ai_cv_related(title, article.get('article_summary', '')):
                            items.append({
                                "title": title,
                                "source": "infoq_cn",
                                "source_name": "InfoQ中文",
                                "url": f"https://www.infoq.cn/article/{article.get('uuid', '')}",
                                "raw_text": article.get('article_summary', ''),
                                "published_at": article.get('publish_time', ''),
                                "meta": {
                                    "author": article.get('author', [{}])[0].get('name', '')
                                }
                            })
        except Exception as e:
            print(f"InfoQ中文 抓取异常：{e}")
        return items
    
    async def _fetch_aliyun(self) -> List[Dict]:
        """抓取阿里云社区"""
        items = []
        try:
            async with self.session.get(
                "https://developer.aliyun.com/group/ai",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # 简单解析 HTML
                    import re
                    pattern = r'<a[^>]*href="(/article/\d+)"[^>]*>\s*<h3[^>]*>(.*?)</h3>'
                    matches = re.findall(pattern, html)
                    for url, title in matches[:10]:
                        if self._is_ai_cv_related(title, ''):
                            items.append({
                                "title": title.strip(),
                                "source": "aliyun",
                                "source_name": "阿里云社区",
                                "url": f"https://developer.aliyun.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"阿里云社区 抓取异常：{e}")
        return items
    
    async def _fetch_medium_ai(self) -> List[Dict]:
        """抓取 Medium AI 标签文章（使用 RSSHub 镜像）"""
        items = []
        try:
            # 使用 RSSHub 的 Medium 路由
            tags = ["artificial-intelligence", "computer-vision", "machine-learning", "ocr"]
            for tag in tags:
                try:
                    async with self.session.get(
                        f"https://rsshub.app/medium/tag/{tag}",
                        headers={'User-Agent': 'Mozilla/5.0'},
                        timeout=15
                    ) as resp:
                        if resp.status == 200:
                            xml_content = await resp.text()
                            items.extend(self._parse_rss_feed(xml_content, f"Medium {tag}"))
                except Exception as e:
                    print(f"Medium tag '{tag}' 抓取异常：{e}")
                    continue
        except Exception as e:
            print(f"Medium AI 抓取异常：{e}")
        return items
    
    def _parse_rss_feed(self, xml_content: str, source_name: str) -> List[Dict]:
        """通用 RSS 解析"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            import re
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                pub_date = item.find('pubDate')
                if title is not None and title.text:
                    title_text = title.text.strip()
                    desc_text = ''
                    if desc is not None and desc.text:
                        desc_text = re.sub(r'<[^>]+>', '', desc.text)[:300]
                    if self._is_ai_cv_related(title_text, desc_text):
                        items.append({
                            "title": title_text,
                            "source": source_name.lower().replace(' ', '_'),
                            "source_name": source_name,
                            "url": link.text.strip() if link is not None and link.text else '',
                            "raw_text": desc_text,
                            "published_at": pub_date.text if pub_date is not None else '',
                            "meta": {}
                        })
        except Exception as e:
            print(f"RSS 解析异常：{e}")
        return items
    
    async def _fetch_tds(self) -> List[Dict]:
        """抓取 Towards Data Science"""
        items = []
        try:
            async with self.session.get(
                "https://towardsdatascience.com/feed",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=15
            ) as resp:
                if resp.status == 200:
                    xml_content = await resp.text()
                    items.extend(self._parse_rss_feed(xml_content, "Towards Data Science"))
        except Exception as e:
            print(f"TDS 抓取异常：{e}")
        return items
    
    async def _fetch_ai_news(self) -> List[Dict]:
        """抓取 AI News (Google)"""
        items = []
        try:
            async with self.session.get(
                "https://news.google.com/rss/search?q=artificial+intelligence+computer+vision+OCR+when:7d",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    xml_content = await resp.text()
                    items.extend(self._parse_google_news_rss(xml_content))
        except Exception as e:
            print(f"AI News 抓取异常：{e}")
        return items
    
    def _parse_google_news_rss(self, xml_content: str) -> List[Dict]:
        """解析 Google News RSS"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                if title is not None:
                    title_text = title.text or ''
                    if self._is_ai_cv_related(title_text, ''):
                        items.append({
                            "title": title_text,
                            "source": "google_news",
                            "source_name": "AI News",
                            "url": link.text if link is not None else '',
                            "raw_text": "",
                            "published_at": pub_date.text if pub_date is not None else '',
                            "meta": {}
                        })
        except Exception as e:
            print(f"Google News RSS 解析异常：{e}")
        return items
    
    async def _fetch_venturebeat(self) -> List[Dict]:
        """抓取 VentureBeat AI"""
        items = []
        try:
            async with self.session.get(
                "https://venturebeat.com/category/ai/feed/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    xml_content = await resp.text()
                    items.extend(self._parse_wp_rss(xml_content, "venturebeat"))
        except Exception as e:
            print(f"VentureBeat 抓取异常：{e}")
        return items
    
    def _parse_wp_rss(self, xml_content: str, source: str) -> List[Dict]:
        """解析 WordPress RSS"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            import re
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                pub_date = item.find('pubDate')
                if title is not None:
                    title_text = title.text or ''
                    desc_text = re.sub(r'<[^>]+>', '', desc.text or '')[:300]
                    if self._is_ai_cv_related(title_text, desc_text):
                        items.append({
                            "title": title_text,
                            "source": source,
                            "source_name": source.capitalize(),
                            "url": link.text if link is not None else '',
                            "raw_text": desc_text,
                            "published_at": pub_date.text if pub_date is not None else '',
                            "meta": {}
                        })
        except Exception as e:
            print(f"WP RSS 解析异常：{e}")
        return items
    
    async def _fetch_lobsters(self) -> List[Dict]:
        """抓取 Lobsters (技术社区)"""
        items = []
        try:
            async with self.session.get(
                "https://lobste.rs/t/ai.rss",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    xml_content = await resp.text()
                    items.extend(self._parse_lobsters_rss(xml_content))
        except Exception as e:
            print(f"Lobsters 抓取异常：{e}")
        return items
    
    def _parse_lobsters_rss(self, xml_content: str) -> List[Dict]:
        """解析 Lobsters RSS"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                if title is not None:
                    title_text = title.text or ''
                    if self._is_ai_cv_related(title_text, ''):
                        items.append({
                            "title": title_text,
                            "source": "lobsters",
                            "source_name": "Lobsters",
                            "url": link.text if link is not None else '',
                            "raw_text": "",
                            "published_at": "",
                            "meta": {}
                        })
        except Exception as e:
            print(f"Lobsters RSS 解析异常：{e}")
        return items
    
    async def _fetch_producthunt(self) -> List[Dict]:
        """抓取 Product Hunt (AI 产品)"""
        items = []
        try:
            async with self.session.get(
                "https://www.producthunt.com/feed?category=artificial-intelligence",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    xml_content = await resp.text()
                    items.extend(self._parse_ph_rss(xml_content))
        except Exception as e:
            print(f"Product Hunt 抓取异常：{e}")
        return items
    
    def _parse_ph_rss(self, xml_content: str) -> List[Dict]:
        """解析 Product Hunt RSS"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                if title is not None:
                    title_text = title.text or ''
                    desc_text = desc.text or ''
                    if self._is_ai_cv_related(title_text, desc_text):
                        items.append({
                            "title": title_text,
                            "source": "producthunt",
                            "source_name": "Product Hunt",
                            "url": link.text if link is not None else '',
                            "raw_text": desc_text[:300],
                            "published_at": "",
                            "meta": {}
                        })
        except Exception as e:
            print(f"PH RSS 解析异常：{e}")
        return items
    
    async def _fetch_gitee(self) -> List[Dict]:
        """抓取 Gitee (国内 GitHub)"""
        items = []
        try:
            queries = [
                "ocr",
                "computer-vision",
                "document-ai",
                "paddleocr"
            ]
            for query in queries:
                async with self.session.get(
                    f"https://gitee.com/api/v5/search/repositories?q={query}&sort=updated&page=1&per_page=10",
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data:
                            updated = repo.get('updated_at', '')
                            try:
                                from dateutil import parser
                                updated_dt = parser.isoparse(updated)
                                days_ago = (datetime.now(updated_dt.tzinfo) - updated_dt).days
                            except:
                                days_ago = 0
                            
                            if days_ago <= 14:
                                items.append({
                                    "title": f"{repo['full_name']}",
                                    "source": "gitee",
                                    "source_name": "Gitee",
                                    "url": repo['html_url'],
                                    "raw_text": repo.get('description', ''),
                                    "published_at": updated,
                                    "meta": {
                                        "stars": repo.get('stargazers_count', 0),
                                        "language": repo.get('language', '')
                                    }
                                })
        except Exception as e:
            print(f"Gitee 抓取异常：{e}")
        return items
    
    async def _fetch_awesome_lists(self) -> List[Dict]:
        """抓取 Awesome Lists (GitHub)"""
        items = []
        try:
            queries = [
                "awesome computer vision",
                "awesome OCR",
                "awesome document understanding",
                "awesome multimodal"
            ]
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            for query in queries:
                async with self.session.get(
                    f"https://api.github.com/search/repositories?q={query}+awesome+stars:>100&sort=updated",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get('items', [])[:5]:
                            items.append({
                                "title": f"{repo['full_name']}",
                                "source": "github_awesome",
                                "source_name": "GitHub Awesome",
                                "url": repo['html_url'],
                                "raw_text": repo.get('description', ''),
                                "published_at": repo.get('updated_at', ''),
                                "meta": {
                                    "stars": repo.get('stargazers_count', 0),
                                    "is_awesome": True
                                }
                            })
        except Exception as e:
            print(f"Awesome Lists 抓取异常：{e}")
        return items
    
    async def _fetch_openreview(self) -> List[Dict]:
        """抓取 OpenReview (会议论文)"""
        items = []
        try:
            # OpenReview API
            async with self.session.get(
                "https://api.openreview.net/notes?invitation=CVPR.*/-/Blind_Submission&limit=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for note in data.get('notes', []):
                        content = note.get('content', {})
                        title = content.get('title', '')
                        abstract = content.get('abstract', '')
                        if self._is_ai_cv_related(title, abstract):
                            items.append({
                                "title": title,
                                "source": "openreview",
                                "source_name": "OpenReview",
                                "url": f"https://openreview.net/forum?id={note.get('forum', '')}",
                                "raw_text": abstract,
                                "published_at": note.get('tcdate', ''),
                                "meta": {
                                    "venue": note.get('invitation', '').split('/')[0]
                                }
                            })
        except Exception as e:
            print(f"OpenReview 抓取异常：{e}")
        return items
    
    async def _fetch_semantic_scholar(self) -> List[Dict]:
        """抓取 Semantic Scholar"""
        items = []
        try:
            # Semantic Scholar API (公开)
            async with self.session.get(
                "https://api.semanticscholar.org/graph/v1/paper/search?query=computer+vision+OCR&limit=20&fields=title,abstract,url,year",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for paper in data.get('data', []):
                        title = paper.get('title', '')
                        abstract = paper.get('abstract', '')
                        if self._is_ai_cv_related(title, abstract):
                            items.append({
                                "title": title,
                                "source": "semantic_scholar",
                                "source_name": "Semantic Scholar",
                                "url": paper.get('url', ''),
                                "raw_text": abstract or '',
                                "published_at": str(paper.get('year', '')),
                                "meta": {
                                    "citationCount": paper.get('citationCount', 0)
                                }
                            })
        except Exception as e:
            print(f"Semantic Scholar 抓取异常：{e}")
        return items
    
    async def _fetch_crossref(self) -> List[Dict]:
        """抓取 Crossref (学术文献)"""
        items = []
        try:
            async with self.session.get(
                "https://api.crossref.org/works?query=computer+vision+OCR&filter=from_pub_date:2024&rows=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for work in data.get('message', {}).get('items', []):
                        title = work.get('title', [''])[0]
                        if self._is_ai_cv_related(title, ''):
                            items.append({
                                "title": title,
                                "source": "crossref",
                                "source_name": "Crossref",
                                "url": work.get('URL', ''),
                                "raw_text": work.get('abstract', '') or '',
                                "published_at": work.get('published-print', {}).get('date-parts', [['']])[0][0],
                                "meta": {
                                    "doi": work.get('DOI', ''),
                                    "type": work.get('type', '')
                                }
                            })
        except Exception as e:
            print(f"Crossref 抓取异常：{e}")
        return items
    
    async def _fetch_twitter_ai(self) -> List[Dict]:
        """抓取 Twitter/X AI 讨论 (通过 Nitter 镜像)"""
        items = []
        try:
            # 使用 Nitter 镜像抓取公开推文
            nitter_hosts = ["nitter.net", "nitter.cz"]
            queries = ["computer vision", "OCR", "multimodal AI"]
            
            for host in nitter_hosts:
                try:
                    for query in queries:
                        async with self.session.get(
                            f"https://{host}/search?f=tweets&q={query.replace(' ', '%20')}&since={datetime.now().strftime('%Y-%m-%d')}",
                            headers={'User-Agent': 'Mozilla/5.0'},
                            timeout=10
                        ) as resp:
                            if resp.status == 200:
                                html = await resp.text()
                                # 简单解析
                                import re
                                pattern = r'<div class="tweet-content[^"]*">.*?<div class="tweet-body">.*?<div[^>]*>(.*?)</div>'
                                matches = re.findall(pattern, html, re.DOTALL)
                                for content in matches[:5]:
                                    text = re.sub(r'<[^>]+>', '', content).strip()
                                    if len(text) > 50 and self._is_ai_cv_related(text, ''):
                                        items.append({
                                            "title": text[:100] + "..." if len(text) > 100 else text,
                                            "source": "twitter",
                                            "source_name": "Twitter/X AI",
                                            "url": f"https://twitter.com/search?q={query.replace(' ', '%20')}",
                                            "raw_text": text,
                                            "published_at": datetime.now().isoformat(),
                                            "meta": {"query": query}
                                        })
                except:
                    continue
        except Exception as e:
            print(f"Twitter AI 抓取异常：{e}")
        return items
    
    async def _fetch_karpathy_rss(self) -> List[Dict]:
        """抓取 Karpathy 推荐的 90 个顶级技术博客 RSS"""
        items = []
        
        # 90 RSS feeds from Hacker News Popularity Contest 2025 (curated by Karpathy)
        # 精选与 AI/CV/技术相关的源
        rss_feeds = [
            # AI/ML 相关
            {"name": "simonwillison.net", "url": "https://simonwillison.net/atom/everything/", "category": "AI"},
            {"name": "garymarcus.substack.com", "url": "https://garymarcus.substack.com/feed", "category": "AI"},
            {"name": "minimaxir.com", "url": "https://minimaxir.com/index.xml", "category": "AI"},
            {"name": "geohot.github.io", "url": "https://geohot.github.io/blog/feed.xml", "category": "AI"},
            {"name": "gwern.net", "url": "https://gwern.substack.com/feed", "category": "AI"},
            
            # 工程/编程
            {"name": "antirez.com", "url": "http://antirez.com/rss", "category": "Engineering"},
            {"name": "matklad.github.io", "url": "https://matklad.github.io/feed.xml", "category": "Engineering"},
            {"name": "eli.thegreenplace.net", "url": "https://eli.thegreenplace.net/feeds/all.atom.xml", "category": "Engineering"},
            {"name": "fabiensanglard.net", "url": "https://fabiensanglard.net/rss.xml", "category": "Engineering"},
            {"name": "overreacted.io", "url": "https://overreacted.io/rss.xml", "category": "Engineering"},
            
            # 安全
            {"name": "krebsonsecurity.com", "url": "https://krebsonsecurity.com/feed/", "category": "Security"},
            {"name": "lcamtuf.substack.com", "url": "https://lcamtuf.substack.com/feed", "category": "Security"},
            {"name": "troyhunt.com", "url": "https://www.troyhunt.com/rss/", "category": "Security"},
            
            # 创业/产品
            {"name": "paulgraham.com", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss", "category": "Startup"},
            {"name": "steveblank.com", "url": "https://steveblank.com/feed/", "category": "Startup"},
            
            # 其他高质量技术博客
            {"name": "daringfireball.net", "url": "https://daringfireball.net/feeds/main", "category": "Tech"},
            {"name": "dynomight.net", "url": "https://dynomight.net/feed.xml", "category": "Tech"},
            {"name": "rachelbythebay.com", "url": "https://rachelbythebay.com/w/atom.xml", "category": "Tech"},
            {"name": "xeiaso.net", "url": "https://xeiaso.net/blog.rss", "category": "Tech"},
            {"name": "dwarkesh.com", "url": "https://www.dwarkeshpatel.com/feed", "category": "Tech"},
            {"name": "mitchellh.com", "url": "https://mitchellh.com/feed.xml", "category": "Tech"},
            {"name": "lucumr.pocoo.org", "url": "https://lucumr.pocoo.org/feed.atom", "category": "Tech"},
            {"name": "skyfall.dev", "url": "https://skyfall.dev/rss.xml", "category": "Tech"},
            {"name": "timsh.org", "url": "https://timsh.org/rss/", "category": "Tech"},
            {"name": "johndcook.com", "url": "https://www.johndcook.com/blog/feed/", "category": "Tech"},
            {"name": "gilesthomas.com", "url": "https://gilesthomas.com/feed/rss.xml", "category": "Tech"},
            {"name": "evanhahn.com", "url": "https://evanhahn.com/feed.xml", "category": "Tech"},
            {"name": "susam.net", "url": "https://susam.net/feed.xml", "category": "Tech"},
            {"name": "buttondown.com/hillelwayne", "url": "https://buttondown.com/hillelwayne/rss", "category": "Tech"},
            {"name": "borretti.me", "url": "https://borretti.me/feed.xml", "category": "Tech"},
            {"name": "jayd.ml", "url": "https://jayd.ml/feed.xml", "category": "Tech"},
            {"name": "blog.jim-nielsen.com", "url": "https://blog.jim-nielsen.com/feed.xml", "category": "Tech"},
            {"name": "jyn.dev", "url": "https://jyn.dev/atom.xml", "category": "Tech"},
            {"name": "geoffreylitt.com", "url": "https://www.geoffreylitt.com/feed.xml", "category": "Tech"},
            {"name": "downtowndougbrown.com", "url": "https://www.downtowndougbrown.com/feed/", "category": "Tech"},
            {"name": "brutecat.com", "url": "https://brutecat.com/rss.xml", "category": "Tech"},
            {"name": "abortretry.fail", "url": "https://www.abortretry.fail/feed", "category": "Tech"},
            {"name": "oldvcr.blogspot.com", "url": "https://oldvcr.blogspot.com/feeds/posts/default", "category": "Tech"},
            {"name": "bogdanthegeek.github.io", "url": "https://bogdanthegeek.github.io/blog/index.xml", "category": "Tech"},
            {"name": "hugotunius.se", "url": "https://hugotunius.se/feed.xml", "category": "Tech"},
            {"name": "berthub.eu", "url": "https://berthub.eu/articles/index.xml", "category": "Tech"},
            {"name": "chadnauseam.com", "url": "https://chadnauseam.com/rss.xml", "category": "Tech"},
            {"name": "simone.org", "url": "https://simone.org/feed/", "category": "Tech"},
            {"name": "it-notes.dragas.net", "url": "https://it-notes.dragas.net/feed/", "category": "Tech"},
            {"name": "beej.us", "url": "https://beej.us/blog/rss.xml", "category": "Tech"},
            {"name": "hey.paris", "url": "https://hey.paris/index.xml", "category": "Tech"},
            {"name": "danielwirtz.com", "url": "https://danielwirtz.com/rss.xml", "category": "Tech"},
            {"name": "matduggan.com", "url": "https://matduggan.com/rss/", "category": "Tech"},
            {"name": "refactoringenglish.com", "url": "https://refactoringenglish.com/index.xml", "category": "Tech"},
            {"name": "worksonmymachine.substack.com", "url": "https://worksonmymachine.substack.com/feed", "category": "Tech"},
            {"name": "philiplaine.com", "url": "https://philiplaine.com/index.xml", "category": "Tech"},
            {"name": "bernsteinbear.com", "url": "https://bernsteinbear.com/feed.xml", "category": "Tech"},
            {"name": "danieldelaney.net", "url": "https://danieldelaney.net/feed", "category": "Tech"},
            {"name": "herman.bearblog.dev", "url": "https://herman.bearblog.dev/feed/", "category": "Tech"},
            {"name": "tomrenner.com", "url": "https://tomrenner.com/index.xml", "category": "Tech"},
            {"name": "blog.pixelmelt.dev", "url": "https://blog.pixelmelt.dev/rss/", "category": "Tech"},
            {"name": "martinalderson.com", "url": "https://martinalderson.com/feed.xml", "category": "Tech"},
            {"name": "danielchasehooper.com", "url": "https://danielchasehooper.com/feed.xml", "category": "Tech"},
            {"name": "chiark.greenend.org.uk/~sgtatham", "url": "https://www.chiark.greenend.org.uk/~sgtatham/quasiblog/feed.xml", "category": "Tech"},
            {"name": "grantslatton.com", "url": "https://grantslatton.com/rss.xml", "category": "Tech"},
            {"name": "experimental-history.com", "url": "https://www.experimental-history.com/feed", "category": "Tech"},
            {"name": "anildash.com", "url": "https://anildash.com/feed.xml", "category": "Tech"},
            {"name": "aresluna.org", "url": "https://aresluna.org/main.rss", "category": "Tech"},
            {"name": "michael.stapelberg.ch", "url": "https://michael.stapelberg.ch/feed.xml", "category": "Tech"},
            {"name": "miguelgrinberg.com", "url": "https://blog.miguelgrinberg.com/feed", "category": "Tech"},
            {"name": "keygen.sh", "url": "https://keygen.sh/blog/feed.xml", "category": "Tech"},
            {"name": "mjg59.dreamwidth.org", "url": "https://mjg59.dreamwidth.org/data/rss", "category": "Tech"},
            {"name": "computer.rip", "url": "https://computer.rip/rss.xml", "category": "Tech"},
            {"name": "tedunangst.com", "url": "https://www.tedunangst.com/flak/rss", "category": "Tech"},
        ]
        
        # 快速失败机制：记录失败次数，连续失败2次则跳过
        failed_feeds = {}  # name -> fail_count
        
        # 并发抓取（限制并发数，缩短超时）
        semaphore = asyncio.Semaphore(10)
        
        async def fetch_single_feed(feed: dict) -> List[Dict]:
            # 检查是否连续失败2次
            if failed_feeds.get(feed["name"], 0) >= 2:
                return []
            
            async with semaphore:
                feed_items = []
                try:
                    # 缩短超时到 8 秒
                    async with self.session.get(
                        feed["url"],
                        headers={'User-Agent': 'Mozilla/5.0'},
                        timeout=aiohttp.ClientTimeout(total=8, connect=5)
                    ) as resp:
                        if resp.status == 200:
                            xml_content = await resp.text()
                            parsed = self._parse_rss_feed(xml_content, feed["name"])
                            for item in parsed:
                                item["meta"]["category"] = feed["category"]
                                item["meta"]["source_type"] = "karpathy_rss"
                            feed_items.extend(parsed)
                            # 成功后重置失败计数
                            failed_feeds[feed["name"]] = 0
                except asyncio.TimeoutError:
                    failed_feeds[feed["name"]] = failed_feeds.get(feed["name"], 0) + 1
                    if failed_feeds[feed["name"]] >= 2:
                        print(f"  ✗ {feed['name']}: 连续超时2次，已跳过")
                    else:
                        print(f"  ⚠️ {feed['name']}: 超时（1/2）")
                except Exception as e:
                    failed_feeds[feed["name"]] = failed_feeds.get(feed["name"], 0) + 1
                    if failed_feeds[feed["name"]] >= 2:
                        print(f"  ✗ {feed['name']}: 连续失败2次，已跳过")
                    else:
                        print(f"  ⚠️ {feed['name']}: {str(e)[:30]}（1/2）")
                return feed_items
        
        # 并发执行所有 RSS 抓取
        tasks = [fetch_single_feed(feed) for feed in rss_feeds]
        results = await asyncio.gather(*tasks)
        
        for feed_items in results:
            items.extend(feed_items)
        
        # 统计跳过的源
        skipped = sum(1 for count in failed_feeds.values() if count >= 2)
        print(f"✅ Karpathy RSS: 从 {len(rss_feeds)} 个源获取 {len(items)} 条（跳过 {skipped} 个失效源）")
        return items
    
    # ==================== 新增数据源（第二批）====================
    
    async def _fetch_stackoverflow(self) -> List[Dict]:
        """抓取 Stack Overflow (AI/CV 标签问题)"""
        items = []
        try:
            tags = ["computer-vision", "opencv", "ocr", "deep-learning", "pytorch", "tensorflow"]
            for tag in tags:
                async with self.session.get(
                    f"https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged={tag}&site=stackoverflow&pagesize=10",
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for q in data.get('items', []):
                            items.append({
                                "title": q.get('title', ''),
                                "source": "stackoverflow",
                                "source_name": f"Stack Overflow [{tag}]",
                                "url": q.get('link', ''),
                                "raw_text": "",
                                "published_at": datetime.fromtimestamp(q.get('creation_date', 0)).isoformat(),
                                "meta": {
                                    "score": q.get('score', 0),
                                    "views": q.get('view_count', 0),
                                    "answers": q.get('answer_count', 0)
                                }
                            })
        except Exception as e:
            print(f"Stack Overflow 抓取异常：{e}")
        return items
    
    async def _fetch_github_discussions(self) -> List[Dict]:
        """抓取 GitHub Discussions"""
        items = []
        try:
            repos = ["pytorch/pytorch", "tensorflow/tensorflow", "opencv/opencv", "PaddlePaddle/PaddleOCR"]
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            for repo in repos:
                async with self.session.get(
                    f"https://api.github.com/repos/{repo}/discussions?per_page=10",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for d in data:
                            if self._is_ai_cv_related(d.get('title', ''), d.get('body', '')):
                                items.append({
                                    "title": d.get('title', ''),
                                    "source": "github_discussions",
                                    "source_name": f"GitHub Discussions [{repo}]",
                                    "url": d.get('html_url', ''),
                                    "raw_text": d.get('body', '')[:300],
                                    "published_at": d.get('created_at', ''),
                                    "meta": {
                                        "comments": d.get('comments', 0),
                                        "reactions": d.get('reactions', {}).get('total_count', 0)
                                    }
                                })
        except Exception as e:
            print(f"GitHub Discussions 抓取异常：{e}")
        return items
    
    async def _fetch_huggingface(self) -> List[Dict]:
        """抓取 Hugging Face (模型和数据集)"""
        items = []
        try:
            # 方法1: 搜索 CV/OCR 相关模型
            search_terms = ["computer-vision", "ocr", "vision", "multimodal", "document-ai"]
            seen = set()
            
            for term in search_terms:
                try:
                    async with self.session.get(
                        f"https://huggingface.co/api/models?search={term}&sort=downloads&direction=-1&limit=10",
                        headers={'User-Agent': 'Mozilla/5.0'},
                        timeout=15
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for model in data:
                                model_id = model.get('modelId', '')
                                if model_id in seen:
                                    continue
                                seen.add(model_id)
                                
                                desc = model.get('description', '') or ''
                                if self._is_ai_cv_related(model_id, desc):
                                    items.append({
                                        "title": f"🤗 {model_id}",
                                        "source": "huggingface",
                                        "source_name": "Hugging Face",
                                        "url": f"https://huggingface.co/{model_id}",
                                        "raw_text": desc[:300],
                                        "published_at": model.get('lastModified', ''),
                                        "meta": {
                                            "downloads": model.get('downloads', 0),
                                            "likes": model.get('likes', 0),
                                            "type": "model"
                                        }
                                    })
                except Exception as e:
                    continue
            
            # 方法2: 搜索数据集
            for term in ["ocr", "document", "vision"]:
                try:
                    async with self.session.get(
                        f"https://huggingface.co/api/datasets?search={term}&sort=downloads&direction=-1&limit=5",
                        headers={'User-Agent': 'Mozilla/5.0'},
                        timeout=15
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for ds in data:
                                ds_id = ds.get('id', '')
                                if ds_id in seen:
                                    continue
                                seen.add(ds_id)
                                
                                desc = ds.get('description', '') or ''
                                if self._is_ai_cv_related(ds_id, desc):
                                    items.append({
                                        "title": f"📊 {ds_id}",
                                        "source": "huggingface",
                                        "source_name": "Hugging Face Datasets",
                                        "url": f"https://huggingface.co/datasets/{ds_id}",
                                        "raw_text": desc[:300],
                                        "published_at": ds.get('lastModified', ''),
                                        "meta": {
                                            "downloads": ds.get('downloads', 0),
                                            "likes": ds.get('likes', 0),
                                            "type": "dataset"
                                        }
                                    })
                except Exception as e:
                    continue
            
            print(f"✅ Hugging Face: {len(items)} 条")
        except Exception as e:
            print(f"Hugging Face 抓取异常：{e}")
        return items
    
    async def _fetch_modelscope(self) -> List[Dict]:
        """抓取 ModelScope (阿里模型平台)"""
        items = []
        try:
            async with self.session.get(
                "https://www.modelscope.cn/api/v1/models?PageSize=30&PageNumber=1",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for model in data.get('Data', []):
                        if self._is_ai_cv_related(model.get('Name', ''), model.get('Description', '')):
                            items.append({
                                "title": model.get('Name', ''),
                                "source": "modelscope",
                                "source_name": "ModelScope",
                                "url": f"https://www.modelscope.cn/models/{model.get('Name', '')}",
                                "raw_text": model.get('Description', ''),
                                "published_at": model.get('ModifiedTime', ''),
                                "meta": {
                                    "downloads": model.get('Downloads', 0),
                                    "tags": model.get('Tags', [])
                                }
                            })
        except Exception as e:
            print(f"ModelScope 抓取异常：{e}")
        return items
    
    async def _fetch_paddle(self) -> List[Dict]:
        """抓取 PaddlePaddle 生态"""
        items = []
        try:
            async with self.session.get(
                "https://api.github.com/search/repositories?q=topic:paddlepaddle+sort:updated&per_page=20",
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for repo in data.get('items', []):
                        items.append({
                            "title": f"🚣 {repo['full_name']}",
                            "source": "paddle",
                            "source_name": "PaddlePaddle 生态",
                            "url": repo['html_url'],
                            "raw_text": repo.get('description', ''),
                            "published_at": repo.get('updated_at', ''),
                            "meta": {
                                "stars": repo.get('stargazers_count', 0),
                                "language": repo.get('language', '')
                            }
                        })
        except Exception as e:
            print(f"PaddlePaddle 抓取异常：{e}")
        return items
    
    async def _fetch_pytorch(self) -> List[Dict]:
        """抓取 PyTorch 相关项目"""
        items = []
        try:
            queries = ["pytorch cv", "pytorch ocr", "pytorch vision"]
            for query in queries:
                async with self.session.get(
                    f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}+sort:updated&per_page=10",
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get('items', []):
                            items.append({
                                "title": f"🔥 {repo['full_name']}",
                                "source": "pytorch",
                                "source_name": "PyTorch 生态",
                                "url": repo['html_url'],
                                "raw_text": repo.get('description', ''),
                                "published_at": repo.get('updated_at', ''),
                                "meta": {
                                    "stars": repo.get('stargazers_count', 0)
                                }
                            })
        except Exception as e:
            print(f"PyTorch 抓取异常：{e}")
        return items
    
    async def _fetch_tensorflow(self) -> List[Dict]:
        """抓取 TensorFlow 相关项目"""
        items = []
        try:
            queries = ["tensorflow cv", "tensorflow ocr", "tensorflow vision"]
            for query in queries:
                async with self.session.get(
                    f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}+sort:updated&per_page=10",
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get('items', []):
                            items.append({
                                "title": f"📊 {repo['full_name']}",
                                "source": "tensorflow",
                                "source_name": "TensorFlow 生态",
                                "url": repo['html_url'],
                                "raw_text": repo.get('description', ''),
                                "published_at": repo.get('updated_at', ''),
                                "meta": {
                                    "stars": repo.get('stargazers_count', 0)
                                }
                            })
        except Exception as e:
            print(f"TensorFlow 抓取异常：{e}")
        return items
    
    async def _fetch_oschina(self) -> List[Dict]:
        """抓取开源中国"""
        items = []
        try:
            async with self.session.get(
                "https://www.oschina.net/action/ajax/get_more_news?newsType=ai",
                headers={'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for news in data.get('news', []):
                        if self._is_ai_cv_related(news.get('title', ''), news.get('summary', '')):
                            items.append({
                                "title": news.get('title', ''),
                                "source": "oschina",
                                "source_name": "开源中国",
                                "url": news.get('url', ''),
                                "raw_text": news.get('summary', ''),
                                "published_at": news.get('publishDate', ''),
                                "meta": {
                                    "views": news.get('viewCount', 0),
                                    "comments": news.get('commentCount', 0)
                                }
                            })
        except Exception as e:
            print(f"开源中国 抓取异常：{e}")
        return items
    
    async def _fetch_segmentfault(self) -> List[Dict]:
        """抓取 SegmentFault"""
        items = []
        try:
            async with self.session.get(
                "https://segmentfault.com/api/timelines?tab=ai",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('data', []):
                        if self._is_ai_cv_related(article.get('title', ''), article.get('excerpt', '')):
                            items.append({
                                "title": article.get('title', ''),
                                "source": "segmentfault",
                                "source_name": "SegmentFault",
                                "url": f"https://segmentfault.com{article.get('url', '')}",
                                "raw_text": article.get('excerpt', ''),
                                "published_at": article.get('createdDate', ''),
                                "meta": {
                                    "votes": article.get('votes', 0),
                                    "views": article.get('views', 0)
                                }
                            })
        except Exception as e:
            print(f"SegmentFault 抓取异常：{e}")
        return items
    
    async def _fetch_v2ex(self) -> List[Dict]:
        """抓取 V2EX"""
        items = []
        try:
            async with self.session.get(
                "https://www.v2ex.com/api/topics/hot.json",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for topic in data:
                        if self._is_ai_cv_related(topic.get('title', ''), topic.get('content', '')):
                            items.append({
                                "title": topic.get('title', ''),
                                "source": "v2ex",
                                "source_name": f"V2EX [{topic.get('node', {}).get('title', '')}]",
                                "url": topic.get('url', ''),
                                "raw_text": topic.get('content', '')[:300],
                                "published_at": datetime.fromtimestamp(topic.get('created', 0)).isoformat(),
                                "meta": {
                                    "replies": topic.get('replies', 0),
                                    "node": topic.get('node', {}).get('name', '')
                                }
                            })
        except Exception as e:
            print(f"V2EX 抓取异常：{e}")
        return items
    
    async def _fetch_rsshub(self) -> List[Dict]:
        """抓取 RSSHub (聚合源)"""
        items = []
        try:
            # RSSHub 路由：GitHub Trending
            rsshub_routes = [
                "github/trending/python/weekly",
                "github/trending/jupyter-notebook/weekly",
            ]
            for route in rsshub_routes:
                async with self.session.get(
                    f"https://rsshub.app/{route}",
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        xml_content = await resp.text()
                        items.extend(self._parse_rsshub_rss(xml_content, route))
        except Exception as e:
            print(f"RSSHub 抓取异常：{e}")
        return items
    
    def _parse_rsshub_rss(self, xml_content: str, route: str) -> List[Dict]:
        """解析 RSSHub RSS"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            import re
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                if title is not None:
                    title_text = title.text or ''
                    desc_text = re.sub(r'<[^>]+>', '', desc.text or '')[:300]
                    if self._is_ai_cv_related(title_text, desc_text):
                        items.append({
                            "title": title_text,
                            "source": "rsshub",
                            "source_name": f"RSSHub [{route}]",
                            "url": link.text if link is not None else '',
                            "raw_text": desc_text,
                            "published_at": "",
                            "meta": {"route": route}
                        })
        except Exception as e:
            print(f"RSSHub RSS 解析异常：{e}")
        return items
    
    async def _fetch_google_scholar(self) -> List[Dict]:
        """抓取 Google Scholar (通过 SerpAPI 或镜像)"""
        items = []
        try:
            # 使用 Scholar RSS (需要解析)
            async with self.session.get(
                "https://scholar.google.com/scholar?q=computer+vision+OCR&hl=en&as_sdt=0,5&as_ylo=2024",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=15
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    # 简单解析搜索结果
                    pattern = r'<h3 class="gs_rt"><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h3>.*?<div class="gs_rs">(.*?)</div>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title, snippet in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title)
                        snippet_clean = re.sub(r'<[^>]+>', '', snippet)
                        if self._is_ai_cv_related(title_clean, snippet_clean):
                            items.append({
                                "title": title_clean,
                                "source": "google_scholar",
                                "source_name": "Google Scholar",
                                "url": url if url.startswith('http') else f"https://scholar.google.com{url}",
                                "raw_text": snippet_clean,
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Google Scholar 抓取异常：{e}")
        return items
    
    async def _fetch_dblp(self) -> List[Dict]:
        """抓取 DBLP (计算机科学文献)"""
        items = []
        try:
            async with self.session.get(
                "https://dblp.org/search/publ/api?q=computer+vision+OCR&h=20&format=json",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for hit in data.get('result', {}).get('hits', {}).get('hit', []):
                        info = hit.get('info', {})
                        title = info.get('title', '')
                        if self._is_ai_cv_related(title, ''):
                            items.append({
                                "title": title,
                                "source": "dblp",
                                "source_name": "DBLP",
                                "url": info.get('ee', ''),
                                "raw_text": "",
                                "published_at": str(info.get('year', '')),
                                "meta": {
                                    "venue": info.get('venue', ''),
                                    "authors": [a.get('text', '') for a in info.get('authors', {}).get('author', [])]
                                }
                            })
        except Exception as e:
            print(f"DBLP 抓取异常：{e}")
        return items
    
    async def _fetch_ieee(self) -> List[Dict]:
        """抓取 IEEE Xplore"""
        items = []
        try:
            async with self.session.get(
                "https://ieeexplore.ieee.org/rest/search?querytext=computer%20vision&rowsPerPage=20&pageNumber=1",
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for record in data.get('records', []):
                        title = record.get('articleTitle', '')
                        if self._is_ai_cv_related(title, record.get('abstract', '')):
                            items.append({
                                "title": title,
                                "source": "ieee",
                                "source_name": "IEEE Xplore",
                                "url": f"https://ieeexplore.ieee.org{record.get('documentLink', '')}",
                                "raw_text": record.get('abstract', ''),
                                "published_at": str(record.get('publicationYear', '')),
                                "meta": {
                                    "publication": record.get('publicationTitle', ''),
                                    "citations": record.get('citationCount', 0)
                                }
                            })
        except Exception as e:
            print(f"IEEE Xplore 抓取异常：{e}")
        return items
    
    async def _fetch_acm(self) -> List[Dict]:
        """抓取 ACM Digital Library"""
        items = []
        try:
            async with self.session.get(
                "https://dl.acm.org/action/doSearch?AllField=computer+vision+OCR&startPage=0&pageSize=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    # 简单解析
                    pattern = r'<span class="hlFld-Title"><a[^>]*href="(/doi/[^"]*)"[^>]*>(.*?)</a></span>'
                    matches = re.findall(pattern, html)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title)
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "acm",
                                "source_name": "ACM DL",
                                "url": f"https://dl.acm.org{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"ACM DL 抓取异常：{e}")
        return items
    
    async def _fetch_nature(self) -> List[Dict]:
        """抓取 Nature AI/ML 文章"""
        items = []
        try:
            async with self.session.get(
                "https://www.nature.com/search?q=computer+vision+machine+learning&order=date_desc",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<article[^>]*>.*?<h3[^>]*>.*?<a[^>]*href="(/articles/[^"]*)"[^>]*>(.*?)</a>.*?</h3>.*?<p[^>]*>(.*?)</p>.*?</article>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title, desc in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        desc_clean = re.sub(r'<[^>]+>', '', desc).strip()
                        if self._is_ai_cv_related(title_clean, desc_clean):
                            items.append({
                                "title": title_clean,
                                "source": "nature",
                                "source_name": "Nature",
                                "url": f"https://www.nature.com{url}",
                                "raw_text": desc_clean,
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Nature 抓取异常：{e}")
        return items
    
    async def _fetch_science(self) -> List[Dict]:
        """抓取 Science 杂志"""
        items = []
        try:
            async with self.session.get(
                "https://www.science.org/action/doSearch?AllField=computer+vision&startPage=0&pageSize=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<div class="card-body">.*?<h3[^>]*>.*?<a[^>]*href="(/doi/[^"]*)"[^>]*>(.*?)</a>.*?</h3>.*?<p[^>]*>(.*?)</p>.*?</div>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title, desc in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        desc_clean = re.sub(r'<[^>]+>', '', desc).strip()
                        if self._is_ai_cv_related(title_clean, desc_clean):
                            items.append({
                                "title": title_clean,
                                "source": "science",
                                "source_name": "Science",
                                "url": f"https://www.science.org{url}",
                                "raw_text": desc_clean,
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Science 抓取异常：{e}")
        return items
    
    async def _fetch_mit_tech(self) -> List[Dict]:
        """抓取 MIT Technology Review"""
        items = []
        try:
            async with self.session.get(
                "https://www.technologyreview.com/topic/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<a[^>]*href="(/\d{4}/[^"]*)"[^>]*class="[^"]*item-title[^"]*"[^>]*>(.*?)</a>'
                    matches = re.findall(pattern, html)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "mit_tech",
                                "source_name": "MIT Tech Review",
                                "url": f"https://www.technologyreview.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"MIT Tech Review 抓取异常：{e}")
        return items
    
    async def _fetch_wired(self) -> List[Dict]:
        """抓取 Wired AI 文章"""
        items = []
        try:
            async with self.session.get(
                "https://www.wired.com/tag/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<a[^>]*href="(/story/[^"]*)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</a>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "wired",
                                "source_name": "Wired",
                                "url": f"https://www.wired.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Wired 抓取异常：{e}")
        return items
    
    async def _fetch_verge(self) -> List[Dict]:
        """抓取 The Verge AI"""
        items = []
        try:
            async with self.session.get(
                "https://www.theverge.com/ai-artificial-intelligence",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<h2[^>]*>.*?<a[^>]*href="(/\d{4}/[^"]*)"[^>]*>(.*?)</a>.*?</h2>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "verge",
                                "source_name": "The Verge",
                                "url": f"https://www.theverge.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"The Verge 抓取异常：{e}")
        return items
    
    async def _fetch_ars(self) -> List[Dict]:
        """抓取 Ars Technica"""
        items = []
        try:
            async with self.session.get(
                "https://arstechnica.com/tag/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<h2[^>]*>.*?<a[^>]*href="(/[^"]*)"[^>]*>(.*?)</a>.*?</h2>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "ars",
                                "source_name": "Ars Technica",
                                "url": f"https://arstechnica.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Ars Technica 抓取异常：{e}")
        return items
    
    async def _fetch_techcrunch(self) -> List[Dict]:
        """抓取 TechCrunch AI"""
        items = []
        try:
            async with self.session.get(
                "https://techcrunch.com/category/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<h2[^>]*>.*?<a[^>]*href="(https://techcrunch.com/\d{4}/[^"]*)"[^>]*>(.*?)</a>.*?</h2>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "techcrunch",
                                "source_name": "TechCrunch",
                                "url": url,
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"TechCrunch 抓取异常：{e}")
        return items
    
    async def _fetch_bloomberg(self) -> List[Dict]:
        """抓取 Bloomberg AI"""
        items = []
        try:
            async with self.session.get(
                "https://www.bloomberg.com/artificial-intelligence",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<a[^>]*href="(/news/articles/[^"]*)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</a>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "bloomberg",
                                "source_name": "Bloomberg",
                                "url": f"https://www.bloomberg.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Bloomberg 抓取异常：{e}")
        return items
    
    async def _fetch_reuters(self) -> List[Dict]:
        """抓取 Reuters AI"""
        items = []
        try:
            async with self.session.get(
                "https://www.reuters.com/technology/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<a[^>]*href="(/technology/[^"]*)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</a>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "reuters",
                                "source_name": "Reuters",
                                "url": f"https://www.reuters.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"Reuters 抓取异常：{e}")
        return items
    
    async def _fetch_cnbc(self) -> List[Dict]:
        """抓取 CNBC AI"""
        items = []
        try:
            async with self.session.get(
                "https://www.cnbc.com/artificial-intelligence/",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    import re
                    pattern = r'<a[^>]*href="(/\d{4}/[^"]*)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</a>'
                    matches = re.findall(pattern, html, re.DOTALL)
                    for url, title in matches[:10]:
                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if self._is_ai_cv_related(title_clean, ''):
                            items.append({
                                "title": title_clean,
                                "source": "cnbc",
                                "source_name": "CNBC",
                                "url": f"https://www.cnbc.com{url}",
                                "raw_text": "",
                                "published_at": "",
                                "meta": {}
                            })
        except Exception as e:
            print(f"CNBC 抓取异常：{e}")
        return items
    
    async def _fetch_qbitai(self) -> List[Dict]:
        """抓取 量子位"""
        items = []
        try:
            async with self.session.get(
                "https://www.qbitai.com/wp-json/wp/v2/posts?per_page=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for post in data:
                        title = post.get('title', {}).get('rendered', '')
                        content = post.get('excerpt', {}).get('rendered', '')
                        if self._is_ai_cv_related(title, content):
                            items.append({
                                "title": title,
                                "source": "qbitai",
                                "source_name": "量子位",
                                "url": post.get('link', ''),
                                "raw_text": re.sub(r'<[^>]+>', '', content),
                                "published_at": post.get('date', ''),
                                "meta": {}
                            })
        except Exception as e:
            print(f"量子位 抓取异常：{e}")
        return items
    
    async def _fetch_aiepoch(self) -> List[Dict]:
        """抓取 新智元"""
        items = []
        try:
            async with self.session.get(
                "https://www.aiepoch.com/api/articles?page=1&limit=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('data', []):
                        if self._is_ai_cv_related(article.get('title', ''), article.get('summary', '')):
                            items.append({
                                "title": article.get('title', ''),
                                "source": "aiepoch",
                                "source_name": "新智元",
                                "url": article.get('url', ''),
                                "raw_text": article.get('summary', ''),
                                "published_at": article.get('publish_time', ''),
                                "meta": {}
                            })
        except Exception as e:
            print(f"新智元 抓取异常：{e}")
        return items
    
    async def _fetch_aitechreview(self) -> List[Dict]:
        """抓取 AI科技评论"""
        items = []
        try:
            async with self.session.get(
                "https://www.aitechreview.com/api/news?page=1&size=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for news in data.get('data', []):
                        if self._is_ai_cv_related(news.get('title', ''), news.get('abstract', '')):
                            items.append({
                                "title": news.get('title', ''),
                                "source": "aitechreview",
                                "source_name": "AI科技评论",
                                "url": news.get('url', ''),
                                "raw_text": news.get('abstract', ''),
                                "published_at": news.get('publish_time', ''),
                                "meta": {}
                            })
        except Exception as e:
            print(f"AI科技评论 抓取异常：{e}")
        return items
    
    async def _fetch_paperweekly(self) -> List[Dict]:
        """抓取 PaperWeekly"""
        items = []
        try:
            async with self.session.get(
                "https://www.paperweekly.me/api/articles?page=1&per_page=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('articles', []):
                        if self._is_ai_cv_related(article.get('title', ''), article.get('summary', '')):
                            items.append({
                                "title": article.get('title', ''),
                                "source": "paperweekly",
                                "source_name": "PaperWeekly",
                                "url": article.get('url', ''),
                                "raw_text": article.get('summary', ''),
                                "published_at": article.get('published_at', ''),
                                "meta": {}
                            })
        except Exception as e:
            print(f"PaperWeekly 抓取异常：{e}")
        return items
    
    async def _fetch_extrememart(self) -> List[Dict]:
        """抓取 极市平台"""
        items = []
        try:
            async with self.session.get(
                "https://www.extrememart.com/api/articles?page=1&limit=20",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for article in data.get('data', []):
                        if self._is_ai_cv_related(article.get('title', ''), article.get('abstract', '')):
                            items.append({
                                "title": article.get('title', ''),
                                "source": "extrememart",
                                "source_name": "极市平台",
                                "url": article.get('url', ''),
                                "raw_text": article.get('abstract', ''),
                                "published_at": article.get('publish_time', ''),
                                "meta": {}
                            })
        except Exception as e:
            print(f"极市平台 抓取异常：{e}")
        return items
    
    def _is_ai_cv_related(self, title: str, content: str) -> bool:
        """检查是否是 AI/CV 相关内容"""
        keywords = [
            'AI', '人工智能', '计算机视觉', 'CV', 'OCR',
            '多模态', 'multimodal', 'VLM', '大模型',
            'LLM', '深度学习', '神经网络', '图像识别',
            '文档理解', '版面分析', '目标检测', '图像分割',
            'vision', 'image', 'detection', 'segmentation',
            'computer vision', 'visual', 'scene understanding'
        ]
        text = (title + ' ' + content).lower()
        return any(kw.lower() in text for kw in keywords)
    
    def _parse_arxiv_xml(self, xml_content: str) -> List[Dict]:
        """解析 arXiv Atom XML"""
        items = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                id_elem = entry.find('atom:id', ns)
                published_elem = entry.find('atom:published', ns)
                if title_elem is not None:
                    title = title_elem.text.strip()
                    summary = summary_elem.text.strip() if summary_elem else ''
                    url = id_elem.text if id_elem else ''
                    published = published_elem.text if published_elem else ''
                    arxiv_id = url.split('/abs/')[-1] if '/abs/' in url else ''
                    items.append({
                        "title": title,
                        "source": "arxiv",
                        "source_name": "arXiv",
                        "url": url,
                        "raw_text": summary,
                        "published_at": published,
                        "meta": {
                            "arxiv_id": arxiv_id,
                            "categories": [c.get('term') for c in entry.findall('atom:category', ns)]
                        }
                    })
        except Exception as e:
            print(f"arXiv XML 解析失败：{e}")
        return items
