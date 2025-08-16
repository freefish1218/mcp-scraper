"""
网络工具模块
"""
import functools
import asyncio
import socket
import ssl
from typing import Callable, Any, TypeVar, cast

# 导入自定义异常
from .exceptions import (
    NetworkError, 
    ConnectionTimeoutError, 
    ConnectionFailedError,
    SSLError,
    ProxyError,
    HTTPError,
    HTTPNotFoundError,
    HTTPForbiddenError,
    HTTPUnauthorizedError,
    HTTPServerError
)

# 类型变量声明
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])


def handle_network_errors(func: F) -> F:
    """
    装饰器：捕获网络相关异常并转换为自定义 NetworkError 异常
    
    适用于同步函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (socket.timeout, TimeoutError) as e:
            raise ConnectionTimeoutError(f"请求超时: {str(e)}", e)
        except socket.gaierror as e:
            raise ConnectionFailedError(f"域名解析失败: {str(e)}", e)
        except ssl.SSLError as e:
            raise SSLError(f"SSL证书验证失败: {str(e)}", e)
        except ConnectionRefusedError as e:
            raise ConnectionFailedError(f"连接被拒绝: {str(e)}", e)
        except ConnectionError as e:
            raise ConnectionFailedError(f"连接错误: {str(e)}", e)
        except OSError as e:
            if "proxy" in str(e).lower():
                raise ProxyError(f"代理错误: {str(e)}", e)
            raise ConnectionFailedError(f"网络操作系统错误: {str(e)}", e)
        # 可能来自 requests 等库的异常
        except Exception as e:
            if any(err_type in str(type(e)) for err_type in ["Timeout", "ConnectionError", "HTTPError", "RequestException"]):
                raise NetworkError(f"网络请求错误: {str(e)}", e)
            raise  # 重新抛出非网络相关的异常
    
    return cast(F, wrapper)

def handle_network_errors_async(func: AsyncF) -> AsyncF:
    """
    装饰器：捕获网络相关异常并转换为自定义 NetworkError 异常
    
    适用于异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            raise ConnectionTimeoutError(f"异步请求超时: {str(e)}", e)
        except (socket.timeout, TimeoutError) as e:
            raise ConnectionTimeoutError(f"请求超时: {str(e)}", e)
        except socket.gaierror as e:
            raise ConnectionFailedError(f"域名解析失败: {str(e)}", e)
        except ssl.SSLError as e:
            raise SSLError(f"SSL证书验证失败: {str(e)}", e)
        except ConnectionRefusedError as e:
            raise ConnectionFailedError(f"连接被拒绝: {str(e)}", e)
        except ConnectionError as e:
            raise ConnectionFailedError(f"连接错误: {str(e)}", e)
        except OSError as e:
            if "proxy" in str(e).lower():
                raise ProxyError(f"代理错误: {str(e)}", e)
            raise ConnectionFailedError(f"网络操作系统错误: {str(e)}", e)
        # 可能来自 aiohttp 等库的异常
        except Exception as e:
            if any(err_type in str(type(e)) for err_type in ["Timeout", "ClientConnector", "ClientResponse", "ClientError"]):
                raise NetworkError(f"异步网络请求错误: {str(e)}", e)
            raise  # 重新抛出非网络相关的异常
    
    return cast(AsyncF, wrapper)

def handle_http_errors(func: F) -> F:
    """
    装饰器：捕获HTTP状态码错误并转换为对应的异常
    
    适用于同步函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 检查是否是 requests.HTTPError 或其他HTTP错误
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 404:
                    raise HTTPNotFoundError(f"页面未找到: {str(e)}", e)
                elif status_code == 403:
                    raise HTTPForbiddenError(f"访问被禁止: {str(e)}", e)
                elif status_code == 401:
                    raise HTTPUnauthorizedError(f"未授权访问: {str(e)}", e)
                elif 500 <= status_code < 600:
                    raise HTTPServerError(f"服务器错误 {status_code}: {str(e)}", status_code, e)
                else:
                    raise HTTPError(f"HTTP错误 {status_code}: {str(e)}", status_code, e)
            raise  # 重新抛出非HTTP相关的异常
    
    return cast(F, wrapper)

def handle_http_errors_async(func: AsyncF) -> AsyncF:
    """
    装饰器：捕获HTTP状态码错误并转换为对应的异常
    
    适用于异步函数，需要结合 handle_network_errors_async 使用
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # 检查是否是 aiohttp.ClientResponseError 或其他HTTP错误
            if hasattr(e, 'status'):
                status_code = e.status
                if status_code == 404:
                    raise HTTPNotFoundError(f"页面未找到: {str(e)}", e)
                elif status_code == 403:
                    raise HTTPForbiddenError(f"访问被禁止: {str(e)}", e)
                elif status_code == 401:
                    raise HTTPUnauthorizedError(f"未授权访问: {str(e)}", e)
                elif 500 <= status_code < 600:
                    raise HTTPServerError(f"服务器错误 {status_code}: {str(e)}", status_code, e)
                else:
                    raise HTTPError(f"HTTP错误 {status_code}: {str(e)}", status_code, e)
            # 检查是否是 requests.HTTPError
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 404:
                    raise HTTPNotFoundError(f"页面未找到: {str(e)}", e)
                elif status_code == 403:
                    raise HTTPForbiddenError(f"访问被禁止: {str(e)}", e)
                elif status_code == 401:
                    raise HTTPUnauthorizedError(f"未授权访问: {str(e)}", e)
                elif 500 <= status_code < 600:
                    raise HTTPServerError(f"服务器错误 {status_code}: {str(e)}", status_code, e)
                else:
                    raise HTTPError(f"HTTP错误 {status_code}: {str(e)}", status_code, e)
            raise  # 重新抛出非HTTP相关的异常
    
    return cast(AsyncF, wrapper)


def exception_to_type(exception: Exception):
    """
    将异常对象转换为ExceptionType枚举值
    
    Args:
        exception: 异常对象
        
    Returns:
        ExceptionType: 对应的异常类型枚举值
    """
    from scraper.models import ExceptionType
    from .exceptions import InvalidContentTypeError
    
    if isinstance(exception, HTTPNotFoundError):
        return ExceptionType.NOT_FOUND
    elif isinstance(exception, HTTPForbiddenError):
        return ExceptionType.FORBIDDEN
    elif isinstance(exception, HTTPUnauthorizedError):
        return ExceptionType.UNAUTHORIZED
    elif isinstance(exception, HTTPServerError):
        return ExceptionType.SERVER_ERROR
    elif isinstance(exception, ConnectionTimeoutError):
        return ExceptionType.TIMEOUT
    elif isinstance(exception, SSLError):
        return ExceptionType.SSL_ERROR
    elif isinstance(exception, InvalidContentTypeError):
        return ExceptionType.INVALID_CONTENT_TYPE
    elif isinstance(exception, NetworkError):
        return ExceptionType.NETWORK
    else:
        return ExceptionType.OTHER
