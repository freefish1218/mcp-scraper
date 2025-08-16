"""
scrapling 包的补丁模块
此模块包含:
1. 对 scrapling.parser 模块中 get_all_text 函数的补丁。
2. 对 scrapling.fetchers 模块中 PlayWrightFetcher.async_fetch 函数的补丁。
3. Docker环境下的Playwright浏览器启动参数优化
"""

# 标准库导入
from .get_all_text import patched_get_all_text

# 本地导入
from scraper.utils.logger import get_logger
logger = get_logger('patches', level="INFO")


def apply_patch() -> None:
    """
    应用所有补丁
    
    在应用补丁前会检查是否已经应用过补丁，避免重复应用。
    """
    try:        
        # 确保 scrapling.parser 模块已加载
        import scrapling.parser  # noqa: F811
        from scrapling.parser import Adaptor

        # 确保 scrapling.fetchers 模块已加载
        import scrapling.fetchers  # noqa: F811
        from scrapling.fetchers import AsyncFetcher, PlayWrightFetcher
        
        # 保存原始函数引用，以便在需要时恢复
        if not hasattr(scrapling.parser, '_original_get_all_text'):
            scrapling.parser._original_get_all_text = Adaptor.get_all_text
        
        if not hasattr(scrapling.fetchers, '_original_asyncfetcher_get'):
            scrapling.fetchers._original_asyncfetcher_get = AsyncFetcher.get

        if not hasattr(scrapling.fetchers, '_original_playwright_async_fetch'):
            scrapling.fetchers._original_playwright_async_fetch = PlayWrightFetcher.async_fetch
        
        # 应用补丁
        Adaptor.get_all_text = patched_get_all_text
        logger.info("成功应用 scrapling.parser.get_all_text 补丁，支持增强的 ignore_tags 参数")
                
        return None
        
    except ImportError as e:
        logger.error(f"无法导入 scrapling 模块: {e}")
    except Exception as e:
        logger.error(f"应用补丁时发生错误: {e}", exc_info=True)
