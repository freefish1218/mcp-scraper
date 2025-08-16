"""
工具模块包

提供各种辅助功能，包括文本处理、URL处理、文件操作和日志记录
"""

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)

# 导入所有子模块的公共接口
from .url import normalize_url, format_filename, generate_title_from_url, extract_base_domain, get_ext_by_url
from ..storage import DiskCache, custom_scrape_cache_key, rate_limited
from .logger import get_logger
from .network import handle_http_errors, handle_http_errors_async, handle_network_errors, handle_network_errors_async, exception_to_type
from .exceptions import NetworkError


# 为了向后兼容，保留原有的导入路径
__all__ = [
    'normalize_url', 'format_filename', 'generate_title_from_url', 'extract_base_domain', 'get_ext_by_url',
    'DiskCache', 'custom_scrape_cache_key', 'rate_limited',
    'get_logger',
    'handle_http_errors',
    'handle_http_errors_async',
    'handle_network_errors',
    'handle_network_errors_async',
    'exception_to_type',
    'NetworkError',
]
