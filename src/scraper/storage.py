"""
缓存模块 - 用于缓存抓取及解析的数据
"""

import time
from pathlib import Path
from diskcache import FanoutCache
from diskcache.core import args_to_key
from functools import wraps

from scraper.models import ScraperConfig
from .utils.url import format_filename
from .utils.logger import get_logger

logger = get_logger("scraper.storage")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
# 项目缓存目录
CACHE_DIR = PROJECT_ROOT / "cache"


class DiskCache:
    """
    DiskCache类 - 封装FanoutCache的功能，提供更灵活的接口
    """
    
    def __init__(
        self,
        directory: str = "",  # 缓存路径
        timeout: int = 3600*24*7,  # 默认7天过期
        size_limit: float = 5e9,  # 限制缓存大小为5G
        shards: int = 64,  # 分片数，提高并发性能
        eviction_policy: str = 'least-recently-used',  # 淘汰策略
        **kwargs  # 其他FanoutCache支持的参数
    ):
        """
        初始化DiskCache实例
        
        参数:
            directory: 缓存目录路径
            timeout: 缓存项默认超时时间（秒）
            size_limit: 缓存大小限制（字节）
            shards: 分片数量，用于提高并发性能
            eviction_policy: 缓存淘汰策略
            **kwargs: 传递给FanoutCache的其他参数
        """
        if isinstance(directory, str):
            directory = Path(directory)
        
        cache_dir = CACHE_DIR
        if directory:
            cache_dir = CACHE_DIR / directory
            
        # 确保缓存目录存在
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化底层FanoutCache
        self.cache = FanoutCache(
            directory=cache_dir,
            timeout=timeout,
            size_limit=size_limit,
            shards=shards,
            eviction_policy=eviction_policy,
            **kwargs
        )
        
        # 添加异步缓存方法
        self.cache.memoize_async = self._memoize_async
        
    # 代理基础缓存操作到内部cache对象
    def get(self, key, read=False, default=None, **kwargs):
        """获取缓存项"""
        return self.cache.get(key, read=read, default=default, **kwargs)
    
    def set(self, key, value, read=False, expire=None, tag=None, **kwargs):
        """设置缓存项"""
        return self.cache.set(key, value, read=read, expire=expire, tag=tag, **kwargs)
        
    def delete(self, key, **kwargs):
        """删除缓存项"""
        return self.cache.delete(key, **kwargs)
        
    def clear(self, **kwargs):
        """清空缓存"""
        return self.cache.clear(**kwargs)
        
    def evict(self, tag=None):
        """根据标签淘汰缓存项"""
        return self.cache.evict(tag)
        
    def memoize(self, *, typed=False, tag=None, expire=None):
        """同步函数的缓存装饰器，代理到内部cache的memoize方法"""
        return self.cache.memoize(typed=typed, tag=tag, expire=expire)


    def _memoize_async(self, *, typed=False, tag=None, expire=None, make_key=None):
        """
        为异步函数提供的缓存装饰器。
        
        参数:
            typed (bool): 是否区分参数类型（例如，区分 f(3) 和 f(3.0)）
            tag (str): 与缓存项关联的标签，用于批量管理
            expire (float): 缓存项的过期时间（秒）
            make_key (callable): 自定义缓存键生成函数，接收和被装饰函数相同的参数
            
        返回:
            装饰器函数
        """
        def decorator(func):
            prefix = func.__qualname__
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if make_key:
                    key = make_key(*args, **kwargs)
                else:
                    # 自定义键生成逻辑，因为 args_to_key 不支持 namespace 参数
                    base_key = args_to_key(args, kwargs, typed=typed)
                    key = f"{prefix}:{base_key}"
                
                # 尝试从缓存获取结果
                result = self.cache.get(key)
                if result is not None:
                    logger.debug(f"缓存命中: {key}")
                    return result
                
                # 执行异步函数并缓存结果
                logger.debug(f"缓存未命中，执行函数: {key}")
                result = await func(*args, **kwargs)
                if result is not None:  # 只缓存非 None 结果
                    self.cache.set(key, result, expire=expire, tag=tag)
                
                return result
            
            # 添加缓存键生成函数属性，方便调试
            if make_key:
                wrapper.__cache_key__ = make_key
            else:
                wrapper.__cache_key__ = lambda *args, **kwargs: f"{prefix}:{args_to_key(args, kwargs, typed=typed)}"
            return wrapper
        
        return decorator
    
    def memoize_async(self, *, typed=False, tag=None, expire=None, make_key=None):
        """
        为异步函数提供的缓存装饰器。
        
        参数:
            typed (bool): 是否区分参数类型（例如，区分 f(3) 和 f(3.0)）
            tag (str): 与缓存项关联的标签，用于批量管理
            expire (float): 缓存项的过期时间（秒）
            make_key (callable): 自定义缓存键生成函数，接收和被装饰函数相同的参数
            
        返回:
            装饰器函数
        """
        return self._memoize_async(typed=typed, tag=tag, expire=expire, make_key=make_key)



def custom_scrape_cache_key(instance, url):
    """
    为 ArticleScraper.scrape 方法创建自定义缓存键。
    键基于 URL 和实例配置中的相关字段。
    
    参数:
        instance: ArticleScraper 实例
        url: 要抓取的URL
        
    返回:
        str: 生成的缓存键
    """
    # 这里的 instance 就是 ArticleScraper 的实例
    config: ScraperConfig = instance.config
    file_name = format_filename(url)
    
    # 使用稳定的键生成方式，不依赖 hash()
    config_parts = str(tuple([
        config.min_content_length,
        config.use_browser,
        config.referer,
        config.llm_summary,
    ]))
    key = f"scrape:{file_name}:{config_parts}"
    logger.debug(f"使用缓存键: {key}")
    return key


def dynamic_scrape_cache_key(
    url: str,
    headless: bool = True,
    timeout: int = 10000,
    max_retries: int = 2,
    use_browser: bool = False,
    referer: str = None,
    llm_summary: bool = False
):
    """
    为动态参数的 scrape 方法创建缓存键
    基于 URL 和所有影响抓取结果的参数
    
    参数:
        url: 要抓取的URL
        headless: 是否使用无头模式
        timeout: 超时时间（毫秒）
        max_retries: 最大重试次数
        use_browser: 是否强制使用浏览器抓取
        referer: 来源URL
        llm_summary: 是否启用自动总结
        
    返回:
        str: 生成的缓存键
    """
    file_name = format_filename(url)
    
    # 只包含影响抓取结果的参数（timeout 和 max_retries 不影响最终结果）
    cache_params = str(tuple([
        use_browser,
        referer,
        llm_summary,
    ]))
    
    key = f"scrape_dynamic:{file_name}:{cache_params}"
    logger.debug(f"使用动态缓存键: {key}")
    return key


def rate_limited(max_per_second):
    """
    限制函数调用频率的装饰器
    
    参数:
        max_per_second: 每秒最大调用次数
        
    返回:
        装饰器函数
    """
    min_interval = 1.0 / max_per_second
    def decorator(func):
        last_called = 0
        @wraps(func)  # 正确使用wraps，修复之前的集成问题
        def wrapper(*args, **kwargs):
            nonlocal last_called
            elapsed = time.time() - last_called
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"限速: 休眠 {sleep_time:.4f} 秒")
                time.sleep(sleep_time)
            last_called = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
