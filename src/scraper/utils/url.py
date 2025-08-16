"""
URL处理工具模块
提供URL标准化和文件名格式化功能
"""

import re
import os
import hashlib
import tldextract
from typing import Optional
from urllib.parse import urlparse

from .logger import get_logger

# 创建工具模块的logger
logger = get_logger("utils.url", level=os.getenv("LOG_LEVEL", "INFO"))


def extract_base_domain(url: str) -> str:
    """
    从URL中提取基础域名（注册域名）
    
    使用 tldextract 库提取域名中的注册部分，能够正确处理各种复杂情况：
    - 多级域名 (example.co.uk, example.gov.cn)
    - 常见子域名 (www.example.com -> example.com)
    - 新顶级域名 (.app, .dev 等)
    - 国际化域名 (IDN)
    - 云平台域名 (保留完整的服务域名，如 oss-cn-north-2-gov-1.aliyuncs.com)
    
    Args:
        url: 需要处理的 URL
        
    Returns:
        str: 提取的注册域名，如 'example.com', 'example.co.uk', 'example.gov.cn' 等
             对于云平台，返回完整的服务域名
    """
    try:
        # 使用 tldextract 解析 URL
        ext = tldextract.extract(url)
        
        # 定义云平台的注册域名列表
        cloud_platforms = [
            'aliyuncs.com',
            'amazonaws.com', 
            'azure.com',
            'azurewebsites.net',
            'cloudfront.net',
            'googleapis.com',
            'googleusercontent.com',
            'qiniudn.com',
            'qiniu.com',
            '126.net',
            '163.com',
            'sinaimg.cn',
            'hdslb.com',  # bilibili
            'githubassets.com',
            'githubusercontent.com'
        ]
        
        # 构建注册域名 (registered domain)
        if ext.domain and ext.suffix:
            registered_domain = f"{ext.domain}.{ext.suffix}"
            
            # 检查是否为云平台域名
            is_cloud_platform = any(registered_domain.endswith(platform) for platform in cloud_platforms)
            
            if is_cloud_platform and ext.subdomain:
                # 对于云平台，返回完整的服务域名（包含子域名）
                full_domain = f"{ext.subdomain}.{registered_domain}"
                logger.debug(f"从 {url} 提取云平台完整域名: {full_domain}")
                return full_domain
            else:
                # 对于普通域名，移除常见的 www 前缀
                if ext.subdomain == 'www':
                    logger.debug(f"从 {url} 提取注册域名: {registered_domain}")
                    return registered_domain
                elif ext.subdomain:
                    # 保留其他子域名
                    full_domain = f"{ext.subdomain}.{registered_domain}"
                    logger.debug(f"从 {url} 提取完整域名: {full_domain}")
                    return full_domain
                else:
                    logger.debug(f"从 {url} 提取注册域名: {registered_domain}")
                    return registered_domain
                    
        elif ext.netloc:  # 无法正确解析时回退到 netloc
            logger.debug(f"无法提取注册域名，使用 netloc: {ext.netloc}")
            return ext.netloc
        else:  # 最后回退到原始 netloc
            parsed_url = urlparse(url)
            return parsed_url.netloc
    except Exception as e:
        logger.warning(f"提取域名失败: {e}")
        return ""


def get_ext_by_url(url: str) -> Optional[str]:
    """
    通过URL得到文件扩展名
    """
    # 解析URL路径
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # 从路径中提取文件名
    filename = os.path.basename(path)
    
    # 如果文件名包含查询参数，去除
    if '?' in filename:
        filename = filename.split('?')[0]
    
    # 提取扩展名
    _, ext = os.path.splitext(filename.lower())
    
    if ext:
        logger.debug(f"URL: {url}")
        logger.debug(f"通过URL确定文件类型: {ext}")
        return ext
    return None


def is_image_url(url: str) -> bool:
    """
    判断URL是否为图片URL
    """
    # 常见图片扩展名
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff']
    url_lower = url.lower()
    ext = get_ext_by_url(url_lower)
    
    if ext in image_extensions:
        return True
    
    if '?format=image' in url_lower:
        return True
    if '/images/' in url_lower:
        return True
    if '/image/' in url_lower:
        return True

    # 检查是否包含图片扩展名后跟着参数（使用正则表达式匹配各种可能的分隔符）
    for ext in image_extensions:
        if re.search(f"{ext}[\\?_\\-@\\d].*$", url_lower):
            return True
    
    return False


def normalize_image_url(url: str) -> str:
    """
    标准化图片URL，移除所有参数
    """
    # 使用正则表达式匹配图片扩展名后面的所有内容
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff']
    ext_pattern = '|'.join(image_extensions)
    
    # 匹配图片URL中的基础部分（移除所有参数）
    match = re.search(f"(.*\.({ext_pattern}))[\\?_\\-@\\d].*$", url.lower())
    if match:
        # 从原始URL中提取到匹配位置的部分（保持原始大小写）
        end_pos = match.span(1)[1]
        return url[:end_pos]
    
    # 如果没有匹配到参数，返回原始URL
    return url


def normalize_regular_url(url: str) -> str:
    """
    标准化普通URL，移除跟踪参数
    """    
    # 移除常见跟踪参数
    tracking_params = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'ocid', 'ncid', 'ref', 'referrer', 'source', 'clickfrom'
    ]

    if '?' in url:
        base_url, query = url.split('?', 1)
        params = query.split('&')
        filtered_params = []
        
        for param in params:
            if '=' in param:
                name, value = param.split('=', 1)
                if name.lower() not in tracking_params:
                    filtered_params.append(f"{name}={value}")
            else:
                filtered_params.append(param)
        
        if filtered_params:
            return f"{base_url}?{'&'.join(filtered_params)}"
        else:
            return base_url
    
    return url


def normalize_url(url: str) -> str:
    """
    标准化URL，移除跟踪参数等
    """

    # 移除URL片段（#后面的内容）
    url = url.split('#')[0]
    
    # 根据URL类型分别处理
    if is_image_url(url):
        return normalize_image_url(url)
    else:
        return normalize_regular_url(url)


def generate_title_from_url(url: str) -> str:
    """从URL生成标题"""
    try:
        # 移除查询参数和片段
        clean_url = url.split('?')[0].split('#')[0]
        # 取路径最后一部分
        path_parts = clean_url.rstrip('/').split('/')
        leaf = path_parts[-1] if path_parts[-1] else path_parts[-2] if len(path_parts) > 1 else clean_url
        # 去除文件扩展名
        if '.' in leaf:
            title = leaf.rsplit('.', 1)[0]
        else:
            title = leaf
        # 将连字符替换为空格
        return re.sub(r'[-_]', ' ', title).title()
    except Exception as e:
        logger.debug(f"提取URL叶子节点失败: {e}, 使用原始URL")
        return url


def format_filename(url: str, title: Optional[str] = None, max_length: int = 100) -> str:
    """
    根据URL和标题生成文件名
    """
    url = url.lower() # 确保URL小写处理

    # 从URL中提取域名
    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
    domain = domain.group(1) if domain else 'unknown'
    
    # 清理域名
    domain = domain.replace('.', '_')
    
    # 如果有标题，使用标题；否则使用URL的一部分
    if title:
        # 移除非法字符
        clean_title = re.sub(r'[\\/*?:"<>|]', '', title)
        # 移除多余空格
        clean_title = re.sub(r'\s+', '_', clean_title.strip())
    else:
        # 构建文件名部分，包含路径和所有查询参数
        path_part = ""
        
        # 提取路径部分
        path = re.search(r'https?://(?:www\.)?[^/]+(/[^?#]+)', url)
        if path:
            path_part = path.group(1).replace('/', '_')
        else:
            path_part = 'homepage'
        
        # 提取所有查询参数
        query_part = ""
        query_string = re.search(r'\?([^#]+)', url)
        if query_string:
            # 将查询字符串分解为参数对
            params = query_string.group(1).split('&')
            for param in params:
                if '=' in param:
                    key, value = param.split('=', 1)
                    # 将每个参数添加到查询部分
                    query_part += f"_{key}_{value}"
                else:
                    # 处理没有值的参数
                    query_part += f"_{param}"
        
        # 组合路径和查询参数
        clean_title = f"{path_part}{query_part}"
    
    # 组合文件名
    filename = f"{domain}_{clean_title}"
    
    # 截断过长的文件名
    if len(filename) > max_length:
        # 保留域名部分，用哈希替换其余部分
        domain_part = domain[:30] if len(domain) > 30 else domain
        hash_part = hashlib.md5(filename.encode()).hexdigest()[:40]
        filename = f"{domain_part}_{hash_part}"    

    return filename
