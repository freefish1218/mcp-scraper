"""
数据模型模块

整合了抓取器的所有数据模型，包括文章数据模型和配置模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field

# ============================================================================
# 参数配置模型定义
# ============================================================================

class ScraperConfig(BaseModel):
    """抓取器参数配置
    
    使用Pydantic模型来定义配置，提供数据验证和序列化功能
    """

    # 基础设置, 开放给用户配置
    headless: bool = Field(default=True, description="无头模式")
    timeout: int = Field(default=10000, description="超时时间（毫秒）", ge=1000, le=60000)
    max_retries: int = Field(default=2, description="最大重试次数", ge=0)
    use_browser: bool = Field(default=False, description="是否强制使用浏览器抓取")
    referer: Optional[str] = Field(default=None, description="来源URL, 比如https://www.google.com/?q=python")
    llm_summary: bool = Field(default=False, description="是否启用自动总结")

    # 抓取与解析设置
    wait_for: int = Field(default=1000, description="加载页面等待时间（毫秒）", ge=0)
    min_content_length: int = Field(default=100, description="最小内容长度（字数）", ge=0)
    delay_range: Tuple[float, float] = Field(default=(0.2, 0.8), description="随机延迟范围(秒)")

    class Config:
        """模型配置类"""
        validate_assignment = True
        arbitrary_types_allowed = True

    def to_json(self) -> str:
        """将配置转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ScraperConfig':
        """从字典创建配置对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            新的ScraperConfig实例
        """
        return cls(**config_dict)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ScraperConfig':
        """从JSON字符串创建配置对象
        
        Args:
            json_str: JSON配置字符串
            
        Returns:
            新的ScraperConfig实例
        """
        return cls.model_validate_json(json_str)


# ============================================================================
# 枚举定义
# ============================================================================

class LinkType(str, Enum):
    """链接类型枚举"""
    IMAGE = "image"
    DOCUMENT = "document"
    OTHER = "other"





class ExceptionType(str, Enum):
    """异常类型枚举"""
    NETWORK = "network"          # 网络异常
    NOT_FOUND = "not_found"      # HTTP 404 未找到
    FORBIDDEN = "forbidden"      # HTTP 403 禁止访问
    UNAUTHORIZED = "unauthorized" # HTTP 401 未授权
    SERVER_ERROR = "server_error" # HTTP 5xx 服务器错误
    PARSING = "parsing"          # 解析异常
    TIMEOUT = "timeout"          # 超时异常
    SSL_ERROR = "ssl_error"      # SSL证书错误
    INVALID_CONTENT_TYPE = "invalid_content_type"  # 无效内容类型（非网页内容）
    OTHER = "other"              # 其他异常


# ============================================================================
# 数据模型定义
# ============================================================================

class Link(BaseModel):
    """链接数据模型"""
    url: str = Field(description="链接URL")
    title: str = Field(default="", description="链接名称")
    type: LinkType = Field(default=LinkType.OTHER, description="链接类型")


class FailedUrl(BaseModel):
    """抓取失败的URL记录"""
    url: str = Field(description="失败的URL")
    reason: str = Field(description="失败原因")
    exception_type: ExceptionType = Field(default=ExceptionType.OTHER, description="异常类型，区分网络异常和其他异常")

    def to_json(self) -> str:
        return self.model_dump_json()


class ScrapedArticle(BaseModel):
    """抓取的文章数据"""
    url: str = Field(description="文章URL")
    publish_date: str = Field(default="", description="文章发布日期")
    title: str = Field(default="", description="文章标题")
    content: str = Field(default="", description="文章正文内容")
    links: List[Link] = Field(default_factory=list, description="文章中的链接列表")
    
    # -- begin: 需使用 llm 总结 --
    source: Optional[str] = Field(default=None, description="文章来源")
    summary: Optional[list] = Field(default=None, description="文章摘要")
    # -- end: 需使用 llm 总结 --

    scrape_time: str = Field(default_factory=lambda: datetime.now().isoformat(), description="抓取时间(ISO格式字符串)")
    html: str = Field(default="", description="原始HTML内容")
    
    class Config:
        """模型配置类"""
        validate_assignment = True
        arbitrary_types_allowed = True
        
    def to_json(self) -> str:
        """将配置转换为JSON字符串"""
        return self.model_dump_json()


class ScrapedArticleList(BaseModel):
    """抓取的文章列表"""
    articles: List[ScrapedArticle] = Field(default_factory=list, description="文章列表")
    failed_urls: List[FailedUrl] = Field(default_factory=list, description="抓取失败的URL及原因列表")
    
    class Config:
        """模型配置类"""
        validate_assignment = True
        arbitrary_types_allowed = True
    
    def to_json(self) -> str:
        """将文章列表转换为JSON字符串（包含文章列表和失败URL列表）"""
        return self.model_dump_json()
    
    def get_summary_stats(self) -> dict:
        """
        获取批量抓取结果的统计摘要
        
        Returns:
            包含各种统计信息的字典
        """
        total_urls = len(self.articles) + len(self.failed_urls)
        success_count = len(self.articles)
        failed_count = len(self.failed_urls)
        
        # 异常类型统计
        exception_stats = {}
        for failed in self.failed_urls:
            exc_type = failed.exception_type.value if failed.exception_type else 'unknown'
            exception_stats[exc_type] = exception_stats.get(exc_type, 0) + 1
        
        # 链接统计
        link_stats = {
            'total_links': 0
        }
        
        for article in self.articles:
            if hasattr(article, 'links') and article.links:
                link_stats['total_links'] += len(article.links)
        
        return {
            'summary': {
                'total_urls': total_urls,
                'success_count': success_count,
                'failed_count': failed_count,
                'success_rate': f"{(success_count / total_urls * 100):.1f}%" if total_urls > 0 else "0.0%"
            },
            'exceptions': exception_stats,
            'links': link_stats
        }
    
    def print_summary(self) -> None:
        """打印批量抓取结果的摘要统计"""
        stats = self.get_summary_stats()
        
        print("=" * 60)
        print("📊 批量抓取结果统计")
        print("=" * 60)
        
        # 基本统计
        summary = stats['summary']
        print(f"📋 总体概况:")
        print(f"   总URL数: {summary['total_urls']}")
        print(f"   成功数量: {summary['success_count']}")
        print(f"   失败数量: {summary['failed_count']}")
        print(f"   成功率: {summary['success_rate']}")
        
        # 异常统计
        if stats['exceptions']:
            print(f"\n❌ 异常类型分布:")
            for exc_type, count in stats['exceptions'].items():
                print(f"   {exc_type}: {count}")
        
        # 链接统计
        links = stats['links']
        if links['total_links'] > 0:
            print(f"\n🔗 链接统计:")
            print(f"   总链接数: {links['total_links']}")
        
        print("=" * 60)
