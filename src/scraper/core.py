"""
核心抓取模块

整合了所有的核心抓取组件，包括基础抓取器、网页抓取器、内容提取器、批处理器和文章抓取器

性能优化说明：
- WebFetcherFactory：使用工厂模式提供静态方法，避免重复创建对象实例
- ArticleScraper：全局单例实例，参数通过方法调用传递，实现"创建一次，永久复用"
- 临时对象：ScraperConfig 和 WebFetcher 对象非常轻量，创建开销微乎其微
- 真正开销：网络I/O操作（HTTP请求1-3秒）和浏览器启动（几秒），而非对象创建（微秒级）
"""

import asyncio
import random
import os
from typing import List, Optional, Any, Dict, Callable, Awaitable

from scrapling.fetchers import AsyncFetcher, PlayWrightFetcher
from scrapling.engines.toolbelt import Response
from playwright.async_api import Page

from scraper.models import ScraperConfig, ScrapedArticle, ScrapedArticleList, FailedUrl, ExceptionType
from scraper.extractors import HtmlExtractor
from scraper.utils.headers import get_referer_header
from scraper.utils.network import (
    handle_http_errors_async, handle_network_errors_async, NetworkError, exception_to_type
)
from scraper.utils.exceptions import (
    HTTPNotFoundError, HTTPForbiddenError, HTTPUnauthorizedError, HTTPServerError
)
from scraper.utils.url import normalize_url, generate_title_from_url
from scraper.utils.content_validator import validate_webpage_url, validate_response_content_type
from scraper.utils.exceptions import InvalidContentTypeError
from scraper.storage import DiskCache, custom_scrape_cache_key, dynamic_scrape_cache_key
from scraper.utils.logger import get_logger


# ============================================================================
# 基础抓取器
# ============================================================================

class BaseScraper:
    """
    抓取器基类
    
    所有特定类型的抓取器都应继承此基类，实现共享功能
    """
    
    def __init__(
        self,
        config: Optional[ScraperConfig] = None,
        cache_directory: Optional[str] = None,
        cache_timeout: int = 3600*24*30,  # 30天过期
        cache_size_limit: int = 5e9,  # 5G
    ):
        """
        初始化抓取器基类
        
        Args:
            config: 抓取配置，默认为None时会创建默认配置
            cache_directory: 缓存目录名称，为None时会使用类名作为目录名
            cache_timeout: 缓存超时时间（秒）
            cache_size_limit: 缓存大小限制（字节）
        """
        # 使用提供的配置或创建默认配置
        self.config = config or ScraperConfig()
        
        # 创建日志记录器
        self.logger = get_logger(self.__class__.__name__, level=os.getenv("LOG_LEVEL", "INFO"))
        
        # 初始化缓存
        cache_dir = cache_directory or self.__class__.__name__
        self.cache = DiskCache(
            directory=cache_dir,
            timeout=cache_timeout,
            size_limit=cache_size_limit,
        )
    
    async def add_delay(self) -> None:
        """
        添加随机延迟，避免请求过于频繁
        
        根据配置的 delay_range 添加随机延迟
        """
        delay = random.uniform(*self.config.delay_range)
        self.logger.info(f"等待 {delay:.2f} 秒...")
        await asyncio.sleep(delay)
    
    async def scrape(self, url: str) -> Any:
        """
        抓取方法（需要由子类实现）
        
        Args:
            url: 要抓取的URL
            
        Returns:
            抓取结果，具体类型由子类决定
            
        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("子类必须实现scrape方法")


# ============================================================================
# 网页抓取器工厂（单例模式）
# ============================================================================

class WebFetcherFactory:
    """
    网页抓取器工厂（单例模式）
    
    提供静态方法直接进行网页抓取，避免重复创建 WebFetcher 实例
    """
    
    @staticmethod
    async def fetch_page(url: str, config: ScraperConfig) -> Optional[Response]:
        """
        静态方法：获取页面内容
        
        Args:
            url: 要获取的URL
            config: 抓取配置
            
        Returns:
            Response: 页面响应对象，如果失败则返回None
            
        Raises:
            NetworkError: 当发生网络连接问题时抛出
        """
        # 规范化URL
        normalized_url = normalize_url(url)
        
        referer_value = None
        if config.referer:
            referer_value = get_referer_header(url=normalized_url, referer=config.referer)

        # 确定是否使用浏览器抓取
        use_browser = config.use_browser

        # 开始抓取
        if use_browser:
            logger = get_logger("WebFetcherFactory")
            logger.info(f"使用浏览器抓取: {normalized_url}")
            response = await WebFetcherFactory._fetch_use_browser(normalized_url, config, referer_value)
        else:
            logger = get_logger("WebFetcherFactory")
            logger.info(f"使用HTTP抓取: {normalized_url}")
            response = await WebFetcherFactory._fetch_http(normalized_url, config, referer_value)

            if not response \
                or len(response.html_content) < config.min_content_length \
                or response.status not in (200, 301, 302, 303, 307, 308, 404, 429, 500, 503):
                logger.warning(f"HTTP抓取失败, 尝试浏览器再次抓取: {normalized_url}")
                response = await WebFetcherFactory._fetch_use_browser(normalized_url, config, referer_value)

        # 检查HTTP状态码
        if response and hasattr(response, 'status'):
            status_code = response.status
            logger = get_logger("WebFetcherFactory")
            logger.debug(f"HTTP状态码: {status_code} for {url}")
            
            if status_code == 404:
                logger.error(f"页面未找到 (404): {url}")
                raise HTTPNotFoundError(f"页面未找到: {url}")
            elif status_code == 403:
                logger.error(f"访问被拒绝 (403): {url}")
                raise HTTPForbiddenError(f"访问被拒绝: {url}")
            elif status_code == 401:
                logger.error(f"未授权访问 (401): {url}")
                raise HTTPUnauthorizedError(f"未授权访问: {url}")
            elif status_code >= 500:
                logger.error(f"服务器错误 ({status_code}): {url}")
                raise HTTPServerError(f"服务器错误 ({status_code}): {url}")
            elif status_code >= 400:
                logger.warning(f"客户端错误 ({status_code}): {url}")

        if not response or len(response.html_content) < config.min_content_length:
            logger = get_logger("WebFetcherFactory")
            logger.warning(f"获取页面内容为空: {url}")
            return None

        return response

    @staticmethod
    async def _fetch_http(url: str, config: ScraperConfig, referer: Optional[str] = None) -> Optional[Response]:
        """
        使用HTTP抓取的内部静态方法
        """
        
        request_args = {
            "url": url,
            "timeout": config.timeout / 1000,
            "retries": config.max_retries,
        }

        if referer:
            request_args["headers"] = {"Referer": referer}

        response = await AsyncFetcher.get(**request_args)
        return response

    @staticmethod
    async def _fetch_use_browser(
            url: str, 
            config: ScraperConfig,
            referer: Optional[str] = None,
            page_action: Optional[Callable[[Page], Awaitable[Page]]] = None
    ) -> Optional[Response]:
        """
        使用浏览器抓取的内部静态方法
        """        
        
        request_args = {
            "url": url,
            "stealth": True,
            "hide_canvas": True,
            "real_chrome": True,
            "disable_resources": True,
            "headless": config.headless,
            "timeout": config.timeout,
            "wait": config.wait_for,
        }

        if page_action:
            request_args["page_action"] = page_action

        if referer:
            request_args["google_search"] = False
            request_args["extra_headers"] = {"Referer": referer}
        else:
            request_args["google_search"] = True

        response = await PlayWrightFetcher.async_fetch(**request_args)
        return response


# ============================================================================
# 内容提取器
# ============================================================================

class ContentExtractor:
    """
    内容提取器
    
    负责从响应中提取结构化内容，生成文章数据
    """
    
    def __init__(self):
        """
        初始化内容提取器
        """
        self.html_extractor = HtmlExtractor()
        self.logger = get_logger("ContentExtractor")
    
    async def extract_from_response(
        self, 
        url: str, 
        response: Response, 
        min_content_length: int = 100,
    ) -> Optional[ScrapedArticle]:
        """
        从响应中提取文章内容
        
        Args:
            url: 原始URL
            response: 页面响应对象
            min_content_length: 最小内容长度
            
        Returns:
            ScrapedArticle: 提取的文章数据，如果失败则返回None
        """
        try:
            # 规范化URL
            normalized_url = normalize_url(url)
            
            # 提取内容
            self.logger.info(f"从响应中提取内容: {normalized_url}")
            article = self.html_extractor.extract(url, response, min_content_length)
            
            if not article:
                self.logger.warning(f"提取内容失败: {url}")
                return None
            
            # 确保URL正确
            article.url = normalized_url
            
            # 如果标题为空，使用URL生成
            if not article.title:
                article.title = generate_title_from_url(url)
            
            return article
        except Exception as e:
            self.logger.error(f"提取内容异常: {str(e)}")
            return None


# ============================================================================
# 批量处理器
# ============================================================================

class BatchProcessor:
    """
    批量处理器
    
    负责并发处理多个URL的抓取任务
    """
    
    def __init__(self):
        """
        初始化批量处理器
        """
        self.logger = get_logger("BatchProcessor")
    
    async def process_batch(
        self,
        urls: List[str],
        processor_func: Callable[[str], Awaitable[Any]],
        max_workers: int = 5,
        add_delay_func: Callable[[], Awaitable[None]] = None
    ) -> ScrapedArticleList:
        """
        批量处理多个URL
        
        Args:
            urls: 要处理的URL列表
            processor_func: 处理单个URL的函数
            max_workers: 并发处理的数量，默认为5
            add_delay_func: 添加延迟的函数，默认为None
            
        Returns:
            ScrapedArticleList: 包含成功处理的文章列表和失败URL信息的对象
            
        Raises:
            ValueError: 当max_workers参数小于等于1时抛出
        """
        if max_workers <= 1:
            raise ValueError("max_workers 参数必须大于1")
        
        # 初始化结果对象
        article_list = ScrapedArticleList()
        
        self.logger.info(f"启用并发处理模式，并发数: {max_workers}")
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(max_workers)
        
        async def _process_with_semaphore(url: str) -> Dict[str, Any]:
            """内部辅助函数: 使用信号量控制的处理方法"""
            async with semaphore:
                try:
                    self.logger.info(f"处理 {url}")
                    result = await processor_func(url)
                    
                    if not result:
                        self.logger.warning(f"处理 {url} 未获取到数据")
                        # 返回失败信息
                        return {
                            "status": "failed",
                            "url": url,
                            "reason": "未获取到数据",
                            "exception_type": ExceptionType.OTHER
                        }

                    # 返回成功结果
                    return {
                        "status": "success",
                        "article": result
                    }
                except InvalidContentTypeError as e:
                    self.logger.info(f"处理 {url} 内容类型无效: {str(e)}")
                    # 返回内容类型错误信息
                    return {
                        "status": "failed",
                        "url": url,
                        "reason": str(e),
                        "exception_type": ExceptionType.INVALID_CONTENT_TYPE
                    }
                except NetworkError as e:
                    self.logger.error(f"处理 {url} 网络连接错误: {str(e)}")
                    # 使用辅助函数获取准确的异常类型
                    exception_type = exception_to_type(e)
                    # 返回网络错误信息
                    return {
                        "status": "failed",
                        "url": url,
                        "reason": str(e),
                        "exception_type": exception_type
                    }
                except Exception as e:
                    self.logger.error(f"处理 {url} 失败: {str(e)}")
                    # 对于其他异常，也尝试使用异常分类函数
                    exception_type = exception_to_type(e)
                    # 返回其他错误信息
                    return {
                        "status": "failed",
                        "url": url,
                        "reason": str(e),
                        "exception_type": exception_type
                    }
                finally:
                    # 如果提供了延迟函数，则调用
                    if add_delay_func:
                        await add_delay_func()
        
        # 创建所有任务
        tasks = [_process_with_semaphore(url) for url in urls]
        
        # 并发执行所有任务
        results_list = await asyncio.gather(*tasks)
        
        # 处理结果
        for result in results_list:
            if result["status"] == "success":
                article_list.articles.append(result["article"])
            else:
                failed_url = FailedUrl(
                    url=result["url"],
                    reason=result["reason"],
                    exception_type=result["exception_type"]
                )
                article_list.failed_urls.append(failed_url)
        
        return article_list


# ============================================================================
# 文章抓取器（主抓取器）
# ============================================================================

class ArticleScraper(BaseScraper):
    """
    文章抓取器
    
    负责抓取网页文章和文档，提取结构化内容
    使用组件化设计，将抓取、提取和批处理职责分离
    """
    
    def __init__(self):
        """
        初始化文章抓取器
        
        现在采用无参数初始化，所有配置参数在方法调用时传递
        这样实现了真正的"创建一次，永久复用，参数灵活传递"的设计
        """
        # 调用父类初始化，使用默认配置（仅用于缓存等基础功能）
        super().__init__(config=None, cache_directory="cache")
        
        # 初始化组件 - 注意：这里不再初始化 WebFetcher，因为配置是动态的
        self.extractor = ContentExtractor()
        self.batch_processor = BatchProcessor()
        
        # 重新实现缓存功能，使用动态参数的缓存键
        self._setup_cache()
    
    def _setup_cache(self):
        """
        设置缓存装饰器
        
        为 _scrape_with_cache 方法动态添加缓存装饰器
        """
        # 创建自定义缓存键函数
        def make_cache_key(url, headless=True, timeout=10000, max_retries=2, 
                          use_browser=False, referer=None):
            return dynamic_scrape_cache_key(
                url=url,
                headless=headless,
                timeout=timeout,
                max_retries=max_retries,
                use_browser=use_browser,
                referer=referer
            )
        
        # 为 _scrape_with_cache 方法添加缓存装饰器
        self._scrape_with_cache = self.cache.memoize_async(
            typed=True, 
            tag='scrape_dynamic', 
            make_key=make_cache_key
        )(self._scrape_with_cache)
    
    @handle_network_errors_async
    @handle_http_errors_async
    async def _scrape_with_cache(
        self, 
        url: str,
        headless: bool = True,
        timeout: int = 10000,
        max_retries: int = 2,
        use_browser: bool = False,
        referer: Optional[str] = None
    ) -> Optional[ScrapedArticle]:
        """
        实际执行抓取的内部方法，用于被缓存装饰器包装
        
        此方法会在实例初始化后动态添加缓存装饰器
        
        Args:
            url: 要抓取的URL
            headless: 是否使用无头模式
            timeout: 超时时间（毫秒）
            max_retries: 最大重试次数
            use_browser: 是否强制使用浏览器抓取
            referer: 来源URL
        
        Returns:
            ScrapedArticle: 抓取的文章数据，如果失败则返回None
        
        Raises:
            NetworkError: 当发生网络连接问题时抛出
        """
        try:
            # 去除跟踪参数，标准化URL
            url = normalize_url(url)

            # 1. 验证URL内容类型，确保是网页内容
            validate_webpage_url(url)

            # 2. 创建临时配置
            temp_config = ScraperConfig(
                headless=headless,
                timeout=timeout,
                max_retries=max_retries,
                use_browser=use_browser,
                referer=referer,
            )
            
            # 3. 直接使用工厂方法获取页面内容（零对象创建开销）
            self.logger.info(f"开始获取页面: {url}")
            response = await WebFetcherFactory.fetch_page(url, temp_config)
            if not response:
                self.logger.warning(f"获取页面失败: {url}")
                return None
            
            # 4. 验证响应的Content-Type是否为网页内容
            validate_response_content_type(response)
            
            # 5. 提取文章内容
            self.logger.info(f"开始提取文章内容: {url}")
            article = await self.extractor.extract_from_response(
                url=url,
                response=response,
                min_content_length=temp_config.min_content_length,
            )
            
            # 6. 检查文章数据完整性
            if not article:
                self.logger.warning(f"内容提取失败: {url}")
                return None
            
            self.logger.info(f"文章处理完成: {url}")
            return article
            
        except NetworkError:
            # 网络异常已被装饰器处理并转换，直接向上抛出
            self.logger.error(f"网络连接错误: {url}")
            raise
        except InvalidContentTypeError as e:
            # 内容类型错误需要向上传播，让批量处理器正确处理
            self.logger.error(f"抓取失败: {str(e)}")
            raise
        except Exception as e:
            # 其他非网络相关异常
            self.logger.error(f"抓取失败: {str(e)}")
            return None
    
    async def scrape(
        self, 
        url: str,
        headless: bool = True,
        timeout: int = 10000,
        max_retries: int = 2,
        use_browser: bool = False,
        referer: Optional[str] = None
    ) -> Optional[ScrapedArticle]:
        """
        抓取URL内容（带缓存）
        
        Args:
            url: 要抓取的URL
            headless: 是否使用无头模式
            timeout: 超时时间（毫秒）
            max_retries: 最大重试次数
            use_browser: 是否强制使用浏览器抓取
            referer: 来源URL
            
        Returns:
            ScrapedArticle: 抓取的文章数据，如果失败则返回None
            
        Raises:
            NetworkError: 当发生网络连接问题时抛出
        """
        # 直接调用带缓存的内部方法
        return await self._scrape_with_cache(
            url=url,
            headless=headless,
            timeout=timeout,
            max_retries=max_retries,
            use_browser=use_browser,
            referer=referer
        )


    
    async def bulk_scrape(
        self, 
        urls: List[str], 
        max_workers: int = 5,
        headless: bool = True,
        timeout: int = 10000,
        max_retries: int = 2,
        use_browser: bool = False,
        referer: Optional[str] = None
    ) -> ScrapedArticleList:
        """
        批量抓取多个URL
        
        Args:
            urls: 要抓取的URL列表
            max_workers: 并发抓取的数量, 默认为5
            headless: 是否使用无头模式
            timeout: 超时时间（毫秒）
            max_retries: 最大重试次数
            use_browser: 是否强制使用浏览器抓取
            referer: 来源URL
        
        Returns:
            ScrapedArticleList: 包含成功抓取的文章列表和失败URL信息的对象
            
        Raises:
            ValueError: 当max_workers参数小于等于1时抛出
        """
        self.logger.info(f"开始批量抓取 {len(urls)} 个URL，并发数: {max_workers}")
        
        # 创建参数绑定的处理函数
        async def processor_func_with_params(url: str) -> Optional[ScrapedArticle]:
            return await self.scrape(
                url=url,
                headless=headless,
                timeout=timeout,
                max_retries=max_retries,
                use_browser=use_browser,
                referer=referer
            )
        
        # 使用批处理器执行批量抓取
        return await self.batch_processor.process_batch(
            urls=urls,
            processor_func=processor_func_with_params,  # 传入参数绑定的处理函数
            max_workers=max_workers,   # 并发抓取数量
            add_delay_func=self.add_delay  # 传入延迟函数
        )
    
    def close(self):
        """
        关闭抓取器，清理资源
        """
        self.logger.info("正在清理 ArticleScraper 资源...")
        
        try:
            # 清理缓存
            if hasattr(self, 'cache') and self.cache:
                # DiskCache 使用 cache.cache.close() 来关闭底层 FanoutCache
                if hasattr(self.cache, 'cache'):
                    self.cache.cache.close()
                self.logger.info("缓存已清理")
        except Exception as e:
            self.logger.warning(f"清理缓存时出错: {str(e)}")
        
        # 清理其他组件
        try:
            if hasattr(self, 'extractor'):
                self.extractor = None
            if hasattr(self, 'batch_processor'):
                self.batch_processor = None
                
            self.logger.info("ArticleScraper 资源清理完成")
        except Exception as e:
            self.logger.warning(f"清理组件时出错: {str(e)}")
