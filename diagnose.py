#!/usr/bin/env python3
"""诊断脚本 - 检查 skill 启动问题"""

import sys
from pathlib import Path

print("="*60)
print("AI/CV Weekly 诊断工具")
print("="*60)

# 1. 检查基础导入
print("\n【1】检查基础模块导入...")
try:
    from config_loader import config
    print("✅ config_loader 导入成功")
    print(f"   LLM Model: {config.get('llm.model')}")
    print(f"   API Key: {'已配置' if config.get('llm.api_key') else '未配置'}")
except Exception as e:
    print(f"❌ config_loader 导入失败: {e}")
    sys.exit(1)

try:
    from logger import setup_logger
    setup_logger(level='INFO')
    print("✅ logger 导入并初始化成功")
except Exception as e:
    print(f"❌ logger 导入失败: {e}")

# 2. 检查期号管理器
print("\n【2】检查 IssueManager...")
try:
    from issue_manager import IssueManager
    manager = IssueManager()
    current = manager.peek_current_issue()
    print(f"✅ IssueManager 初始化成功，当前期号: {current}")
except Exception as e:
    print(f"❌ IssueManager 失败: {e}")

# 3. 检查核心模块
print("\n【3】检查核心模块...")
try:
    from core.fetcher import DataFetcher
    print("✅ DataFetcher 导入成功")
except Exception as e:
    print(f"❌ DataFetcher 导入失败: {e}")

try:
    from core.filter import ItemFilter
    print("✅ ItemFilter 导入成功")
except Exception as e:
    print(f"❌ ItemFilter 导入失败: {e}")

try:
    from core.editor import WeeklyEditor
    print("✅ WeeklyEditor 导入成功")
except Exception as e:
    print(f"❌ WeeklyEditor 导入失败: {e}")

try:
    from core.renderer_jinja2 import ReportRenderer
    print("✅ ReportRenderer 导入成功")
except Exception as e:
    print(f"❌ ReportRenderer 导入失败: {e}")

try:
    from core.sender import EmailSender
    print("✅ EmailSender 导入成功")
except Exception as e:
    print(f"❌ EmailSender 导入失败: {e}")

# 4. 检查模板
print("\n【4】检查模板文件...")
template_dir = Path(__file__).parent / "templates"
if template_dir.exists():
    print(f"✅ 模板目录存在: {template_dir}")
    for f in template_dir.glob("*.html"):
        print(f"   - {f.name}")
else:
    print(f"❌ 模板目录不存在: {template_dir}")

# 5. 检查依赖
print("\n【5】检查依赖包...")
try:
    import aiohttp
    print("✅ aiohttp 已安装")
except:
    print("❌ aiohttp 未安装")

try:
    import yaml
    print("✅ PyYAML 已安装")
except:
    print("❌ PyYAML 未安装")

try:
    import jinja2
    print("✅ Jinja2 已安装")
except:
    print("❌ Jinja2 未安装")

try:
    import requests
    print("✅ requests 已安装")
except:
    print("❌ requests 未安装")

try:
    from dateutil import parser
    print("✅ python-dateutil 已安装")
except:
    print("❌ python-dateutil 未安装")

# 6. 尝试初始化 DataFetcher（不实际抓取）
print("\n【6】尝试初始化 DataFetcher...")
try:
    from core.fetcher import DataFetcher
    # 只是初始化，不抓取
    print("✅ DataFetcher 可以初始化")
except Exception as e:
    print(f"❌ DataFetcher 初始化失败: {e}")

print("\n" + "="*60)
print("诊断完成")
print("="*60)
