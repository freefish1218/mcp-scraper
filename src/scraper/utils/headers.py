"""
HTTP 请求头生成工具
"""

from urllib.parse import urlparse
from typing import Optional


def get_referer_header(url: str, referer: Optional[str] = None) -> Optional[str]:
    """
    获取 Referer 头
    
    Args:
        url: 目标URL
        referer: 自定义来源URL
        
    Returns:
        Referer头的值，如果不需要则返回None
    """
    if referer:
        return referer
        
    # 简单的 Referer 生成逻辑
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/"
    
    return None
