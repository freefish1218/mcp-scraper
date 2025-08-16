"""
MCP-Scraper 服务器 (FastMCP 实现版)
提供网页内容抓取、批量处理和语言检测功能
使用 FastMCP 框架实现更简洁的 API
"""

from typing import List, Optional, Annotated
from pathlib import Path
import tomllib

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ToolAnnotations


# 导入项目模块
from scraper.core import ArticleScraper
from scraper.models import ScrapedArticle, ScrapedArticleList
from scraper.utils import get_logger


def get_version_from_pyproject() -> str:
    """
    从 pyproject.toml 文件读取版本号
    
    Returns:
        版本号字符串，读取失败时返回 "unknown"
    """
    try:
        # 获取项目根目录路径（假设 pyproject.toml 在项目根目录）
        current_dir = Path(__file__).parent
        project_root = current_dir.parent  # src 的上一级目录
        pyproject_path = project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            return "unknown"
        
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        
        version = pyproject_data.get("project", {}).get("version")
        return version if version else "unknown"
        
    except (FileNotFoundError, tomllib.TOMLDecodeError, KeyError, OSError) as e:
        # 日志记录在实际运行时才会输出，这里先返回默认值
        return "unknown"
    except Exception:
        # 处理其他可能的异常
        return "unknown"

# 获取版本号
version = get_version_from_pyproject()

# 获取服务器信息
SERVER_INFO = {
    "name": "MCPScraperServer",
    "version": version,
    "description": "专业的网页内容抓取服务，支持单个和批量URL处理、内容提取和语言检测",
    "features": ["单个URL抓取", "批量URL抓取", "内容提取", "语言检测", "LLM自动总结"],
    "instructions": f"这个服务器提供专业的网页内容抓取功能，支持单个和批量URL处理、内容提取和语言检测。当前版本: {version}"
}

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 3001,
    "base_path": "/mcp"  # 基础路径配置
}

# 设置日志
logger = get_logger("mcp.scraper.server")

# 全局抓取器实例
scraper: Optional[ArticleScraper] = None

def get_scraper() -> ArticleScraper:
    """
    创建全局抓取器实例
    
    现在使用完全无参数初始化，实现真正的"创建一次，永久复用"
    所有配置参数在每次方法调用时动态传递，提供最大的灵活性
    
    Returns:
        ArticleScraper: 全局抓取器实例
    """
    logger.info("创建全局抓取器实例...")
    
    # 完全无参数初始化，零配置开销
    scraper = ArticleScraper()
    logger.info("全局抓取器实例创建完成")
    
    return scraper


# 创建 FastMCP 实例
mcp = FastMCP(
    name=SERVER_INFO["name"],
    description=SERVER_INFO["instructions"],
    host=SERVER_CONFIG["host"],
    port=SERVER_CONFIG["port"],
    base_path=SERVER_CONFIG["base_path"], 
    json_response=False, # 使用 SSE 流
    stateless_http=True, # 无状态模式，适合生产部署
)


@mcp.tool(
    description="抓取单个URL并返回文章内容", 
    annotations=ToolAnnotations(
        title="抓取单个URL并返回文章内容", 
        readOnlyHint=True, 
        destructiveHint=False, 
        idempotentHint=True, 
        openWorldHint=True, 
        category="scraper",
    )
)
async def scrape(
    url: Annotated[str, "要抓取的URL地址，支持HTTP和HTTPS协议"], 
    headless: Annotated[bool, "是否使用无头浏览器模式，默认为True"] = True, 
    timeout: Annotated[int, "请求超时时间，单位为毫秒，默认10000ms"] = 10000, 
    max_retries: Annotated[int, "最大重试次数，抓取失败时的重试次数，默认2次"] = 2,
    use_browser: Annotated[bool, "是否强制使用浏览器渲染，适用于动态内容，默认False"] = False,
    referer: Annotated[Optional[str], "HTTP Referer头，用于绕过防盗链检测"] = None,
    llm_summary: Annotated[bool, "是否启用LLM自动总结文章内容，默认False"] = False
) -> List[TextContent]:
    """
    抓取单个URL并返回文章内容
    
    Args:
        url: 要抓取的URL
        headless: 是否使用无头模式
        timeout: 超时时间（毫秒）
        max_retries: 最大重试次数
        use_browser: 是否强制使用浏览器抓取
        referer: 来源URL
        llm_summary: 是否启用自动总结
        
    Returns:
        包含文章内容的文本
    """
    global scraper
    
    logger.info(f"正在抓取URL: {url}")
    
    # 确保全局抓取器已初始化
    if not scraper:
        scraper = get_scraper()
    
    # 直接使用全局抓取器进行抓取，传递参数
    article: Optional[ScrapedArticle] = await scraper.scrape(
        url=url,
        headless=headless,
        timeout=timeout,
        max_retries=max_retries,
        use_browser=use_browser,
        referer=referer,
        llm_summary=llm_summary
    )
    
    logger.info(f"抓取完成: {url}")
    
    if article:
        return [TextContent(type="text", text=article.to_json())]
    else:
        return [TextContent(type="text", text="抓取失败")]


@mcp.tool(
    description="批量抓取多个URL并返回文章内容列表", 
    annotations=ToolAnnotations(
        title="批量抓取多个URL并返回文章内容列表", 
        readOnlyHint=True, 
        destructiveHint=False, 
        idempotentHint=True, 
        openWorldHint=True, 
        category="scraper",
    )
)
async def bulk_scrape(
    urls: Annotated[List[str], "要抓取的URL列表，支持同时处理多个网页"], 
    headless: Annotated[bool, "是否使用无头浏览器模式，默认为True"] = True, 
    timeout: Annotated[int, "单个请求的超时时间，单位为毫秒，默认10000ms"] = 10000, 
    max_retries: Annotated[int, "单个URL的最大重试次数，默认2次"] = 2,
    max_workers: Annotated[int, "并发抓取的工作线程数，控制同时抓取的URL数量，默认5个"] = 5,
    use_browser: Annotated[bool, "是否强制使用浏览器渲染所有URL，适用于动态内容，默认False"] = False,
    referer: Annotated[Optional[str], "HTTP Referer头，应用于所有请求，用于绕过防盗链检测"] = None,
    llm_summary: Annotated[bool, "是否对所有抓取的文章启用LLM自动总结，默认False"] = False
) -> List[TextContent]:
    """
    批量抓取多个URL并返回文章内容列表
    
    Args:
        urls: URL列表
        headless: 是否使用无头模式
        timeout: 超时时间（毫秒）
        max_retries: 最大重试次数
        max_workers: 抓取并发数
        use_browser: 是否强制使用浏览器抓取
        referer: 来源URL
        llm_summary: 是否启用自动总结
        
    Returns:
        包含所有抓取文章的JSON字符串
    """
    global scraper
    
    total_urls = len(urls)
    logger.info(f"开始批量抓取 {total_urls} 个URL")
    
    # 确保全局抓取器已初始化
    if not scraper:
        scraper = get_scraper()
    
    # 直接使用全局抓取器进行批量抓取，传递参数
    article_list: ScrapedArticleList = await scraper.bulk_scrape(
        urls=urls,
        max_workers=max_workers,
        headless=headless,
        timeout=timeout,
        max_retries=max_retries,
        use_browser=use_browser,
        referer=referer,
        llm_summary=llm_summary
    )
    
    logger.info(f"批量抓取完成，成功获取 {len(article_list.articles)} 篇文章")
    
    return [TextContent(type="text", text=article_list.to_json())]


def run_server():
    """
    运行 MCP 服务器
    """
    global scraper
    
    # 获取配置或使用默认值
    host = SERVER_CONFIG.get("host")
    port = SERVER_CONFIG.get("port")
    base_path = SERVER_CONFIG.get("base_path")
    
    logger.info(f"启动 MCP 服务器 - {SERVER_INFO['name']} - 地址: {host}:{port}{base_path}")
    
    try:
        # 在服务器启动前创建全局抓取器实例
        logger.info("初始化全局抓取器实例...")
        scraper = get_scraper()
        
        # 使用 FastMCP 实例的 run 方法启动服务器
        mcp.run(transport="streamable-http",)
        
    except Exception as e:
        logger.error(f"启动服务器失败: {str(e)}")
        raise
    finally:
        if scraper:
            # 确保在服务器关闭时清理资源
            scraper.close()
            scraper = None
