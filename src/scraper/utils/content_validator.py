"""内容类型验证工具模块

提供URL内容类型检测和验证功能
"""

from .url import is_image_url
from .exceptions import InvalidContentTypeError
from ..models import ExceptionType


def is_valid_webpage_url(url: str) -> bool:
    """
    检查URL是否指向有效的网页内容
    
    Args:
        url: 要检查的URL
        
    Returns:
        如果URL指向网页内容则返回True，否则返回False
    """
    # 检查是否为图片URL
    if is_image_url(url):
        return False
            
    # 检查其他非网页内容类型
    non_webpage_extensions = [
        # 文档文件
        '.docx', '.doc', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.pdf', '.txt', '.md', '.markdown',
        # 音频文件
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
        # 视频文件
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        # 压缩文件
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
        # 可执行文件
        '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.app',
        # 其他二进制文件
        '.bin', '.iso', '.img'
    ]
    
    url_lower = url.lower()
    for ext in non_webpage_extensions:
        if url_lower.endswith(ext) or f'{ext}?' in url_lower or f'{ext}#' in url_lower:
            return False
            
    return True


def validate_webpage_url(url: str) -> None:
    """
    验证URL是否为有效的网页内容，如果不是则抛出异常
    
    Args:
        url: 要验证的URL
        
    Raises:
        InvalidContentTypeError: 当URL不是网页内容时
    """
    if not is_valid_webpage_url(url):
        # 确定具体的内容类型
        content_type = "unknown"
        if is_image_url(url):
            content_type = "image"
        else:
            # 尝试从URL扩展名推断类型
            url_lower = url.lower()
            if any(ext in url_lower for ext in ['.docx', '.doc', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.pdf', '.txt', '.md', '.markdown']):
                content_type = "document"
            elif any(ext in url_lower for ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']):
                content_type = "audio"
            elif any(ext in url_lower for ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']):
                content_type = "video"
            elif any(ext in url_lower for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']):
                content_type = "archive"
            elif any(ext in url_lower for ext in ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm']):
                content_type = "executable"
                
        raise InvalidContentTypeError(
            f"URL指向的是{content_type}内容，不是网页: {url}",
            content_type=content_type
        )


def validate_response_content_type(response) -> None:
    """
    验证HTTP响应的Content-Type是否为网页内容
    
    Args:
        response: HTTP响应对象
        
    Raises:
        InvalidContentTypeError: 如果Content-Type不是网页内容
    """
    if not response or not hasattr(response, 'headers'):
        return  # 如果没有headers信息，跳过检查
    
    headers = response.headers
    if not headers:
        return  # 如果headers为空，跳过检查
    
    # 获取Content-Type头
    content_type = headers.get('content-type', '').lower()
    if not content_type:
        return  # 如果没有Content-Type头，跳过检查
    
    # 检查是否为网页内容类型
    webpage_content_types = [
        'text/html',
        'application/xhtml+xml',
        'text/plain'  # 有些网页可能返回text/plain
    ]
    
    # 检查是否为网页内容
    is_webpage = any(ct in content_type for ct in webpage_content_types)
    
    if not is_webpage:
        # 确定具体的内容类型
        if 'image/' in content_type:
            content_desc = "image"
        elif 'application/pdf' in content_type:
            content_desc = "document"
        elif 'application/json' in content_type:
            content_desc = "json"
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            content_desc = "xml"
        elif 'video/' in content_type:
            content_desc = "video"
        elif 'audio/' in content_type:
            content_desc = "audio"
        elif 'application/' in content_type:
            content_desc = "application"
        else:
            content_desc = "non-webpage"
        
        url = getattr(response, 'url', 'unknown')
        raise InvalidContentTypeError(
            f"响应的Content-Type为{content_desc}内容，不是网页: {url} (Content-Type: {content_type})",
            content_type=content_type
        )


def get_content_type_exception_type(url: str) -> ExceptionType:
    """
    根据URL获取对应的异常类型
    
    Args:
        url: 要检查的URL
        
    Returns:
        ExceptionType: 对应的异常类型枚举值
    """
    from scraper.models import ExceptionType
    
    # 目前所有非网页内容都返回相同的异常类型
    # 未来可以根据具体的内容类型返回更细分的异常类型
    return ExceptionType.INVALID_CONTENT_TYPE