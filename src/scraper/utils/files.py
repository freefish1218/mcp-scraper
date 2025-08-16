"""
文件相关工具函数
"""

from urllib.parse import urlparse
from scraper.utils.url import get_ext_by_url


# 支持的文档类型
SUPPORTED_DOC_TYPES = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp']


def is_doc_url(url: str) -> bool:
    """
    判断URL是否指向文档
    
    Args:
        url: 要检查的URL
        
    Returns:
        如果URL可能指向文档则返回True，否则返回False
    """    
    # 解析URL
    ext = get_ext_by_url(url)
    if ext and ext in SUPPORTED_DOC_TYPES:
        return True
    
    # 检查URL参数中是否包含文件下载标识
    parsed_url = urlparse(url)
    query = parsed_url.query.lower()
    
    # 检查查询参数中的下载标识
    query_download_indicators = [
        'download=', 'file=', 'attachment=', 'export=', 'getfile=', 'retrieve=', 'fetch=', 'get=',
        'uuid=', 'file_id=', 'filekey=', 'fileid=', 'filekey=', 'fid=',
        'download=1', 'dl=1', 'save=1', 
        'action=download', 'force_download=true', 'op=get', 'op=download', 'op=export', 'mode=download',
    ]
    for indicator in query_download_indicators:
        if indicator in query:
            return True
    
    # 检查URL路径中是否包含下载关键词
    path = parsed_url.path.lower()
    path_download_indicators = ['download', 'attachment', 'file', 'document', 'export']
    for indicator in path_download_indicators:
        if indicator in path:
            return True

    return False
