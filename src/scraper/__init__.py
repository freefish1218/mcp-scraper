"""
文章抓取模块

提供了从网页抓取结构化内容的功能，支持多种抓取方式
优化后的模块结构，采用分层设计
"""

# 导出核心抓取器
from scraper.core import BaseScraper, ArticleScraper

# 导出提取器
from scraper.extractors import HtmlExtractor

# 导出模型
from scraper.models import (
    ScrapedArticle, 
    ScrapedArticleList, 
    Link, 
    LinkType, 
    ExceptionType, 
    FailedUrl,
    ScraperConfig
)

# 导出工具函数
from scraper.utils.exceptions import NetworkError
from scraper.utils.network import handle_http_errors, handle_http_errors_async, handle_network_errors, handle_network_errors_async
from scraper.utils import get_logger

# 初始化环境变量
import os
from dotenv import load_dotenv
load_dotenv(override=True)

logger = get_logger("scraper", level=os.getenv("LOG_LEVEL", "INFO"))


# 应用补丁
try:
    # 应用 scrapling 补丁
    from patches.playwright_patch import apply_playwright_patch
    from patches.scrapling_patch import apply_patch
    apply_playwright_patch()
    apply_patch()
except ImportError as e:
    logger.warning(f"无法导入补丁模块: {e}")


__all__ = [
    # 核心抓取器
    'BaseScraper', 'ArticleScraper',
    
    # 提取器
    'HtmlExtractor',

    # 模型
    'ScrapedArticle', 'ScrapedArticleList', 'Link', 'LinkType', 'ExceptionType', 'FailedUrl', 'ScraperConfig',
    
    # 工具
    'NetworkError', 'handle_http_errors', 'handle_http_errors_async', 'handle_network_errors', 'handle_network_errors_async'
]
