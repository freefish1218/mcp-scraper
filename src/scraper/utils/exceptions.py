"""
异常定义模块
"""

class NetworkError(Exception):
    """
    网络连接错误的基类
    
    用于统一处理所有网络相关异常
    """
    def __init__(self, message: str = "网络连接错误", original_exception=None):
        self.original_exception = original_exception
        super().__init__(message)
        
class ConnectionTimeoutError(NetworkError):
    """连接超时错误"""
    def __init__(self, message: str = "连接超时", original_exception=None):
        super().__init__(message, original_exception)
        
class ConnectionFailedError(NetworkError):
    """连接失败错误"""
    def __init__(self, message: str = "连接失败", original_exception=None):
        super().__init__(message, original_exception)
        
class SSLError(NetworkError):
    """SSL证书错误"""
    def __init__(self, message: str = "SSL证书验证失败", original_exception=None):
        super().__init__(message, original_exception)
        
class ProxyError(NetworkError):
    """代理错误"""
    def __init__(self, message: str = "代理连接错误", original_exception=None):
        super().__init__(message, original_exception)

class HTTPError(NetworkError):
    """HTTP错误的基类"""
    def __init__(self, message: str = "HTTP请求错误", status_code: int = None, original_exception=None):
        self.status_code = status_code
        super().__init__(message, original_exception)

class HTTPNotFoundError(HTTPError):
    """HTTP 404 错误"""
    def __init__(self, message: str = "页面未找到", original_exception=None):
        super().__init__(message, 404, original_exception)

class HTTPForbiddenError(HTTPError):
    """HTTP 403 错误"""
    def __init__(self, message: str = "访问被禁止", original_exception=None):
        super().__init__(message, 403, original_exception)

class HTTPUnauthorizedError(HTTPError):
    """HTTP 401 错误"""
    def __init__(self, message: str = "未授权访问", original_exception=None):
        super().__init__(message, 401, original_exception)

class HTTPServerError(HTTPError):
    """HTTP 5xx 服务器错误"""
    def __init__(self, message: str = "服务器错误", status_code: int = 500, original_exception=None):
        super().__init__(message, status_code, original_exception)

class InvalidContentTypeError(Exception):
    """无效内容类型错误
    
    当抓取的链接不是网页内容（如图片、文档等）时抛出此异常
    """
    def __init__(self, message: str = "链接内容类型无效，不是网页内容", content_type: str = None, original_exception=None):
        self.content_type = content_type
        self.original_exception = original_exception
        super().__init__(message)
