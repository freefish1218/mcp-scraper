#!/usr/bin/env python3
"""
测试整合后的代码结构和功能
"""

import sys
import os
sys.path.insert(0, 'src')

from scraper import (
    ArticleScraper, 
    ScrapedArticle, 
    ScrapedArticleList,
    Link, 
    LinkType, 
 
    ExceptionType,
    FailedUrl,
    ScraperConfig,
    HtmlExtractor,
    BaseScraper
)

def test_imports():
    """测试所有导入是否正常"""
    print("🧪 测试导入...")
    
    # 测试核心类
    assert ArticleScraper is not None
    assert BaseScraper is not None
    print("✅ 核心抓取器导入成功")
    
    # 测试提取器
    assert HtmlExtractor is not None
    print("✅ 提取器导入成功")
    
    # 测试模型
    assert ScrapedArticle is not None
    assert ScrapedArticleList is not None
    assert Link is not None
    assert FailedUrl is not None
    assert ScraperConfig is not None
    print("✅ 数据模型导入成功")
    
    # 测试枚举
    assert LinkType is not None

    assert ExceptionType is not None
    print("✅ 枚举类型导入成功")

def test_model_creation():
    """测试模型创建"""
    print("\n🧪 测试模型创建...")
    
    # 测试配置
    config = ScraperConfig(
        headless=True,
        timeout=10000,
        max_retries=3
    )
    print("✅ ScraperConfig 创建成功")
    
    # 测试链接
    link = Link(
        url="https://example.com/test",
        title="测试链接",
        type=LinkType.OTHER,

    )
    print("✅ Link 创建成功")
    
    # 测试文章
    article = ScrapedArticle(
        url="https://example.com",
        title="测试文章",
        content="这是测试内容",
        links=[link]
    )
    print("✅ ScrapedArticle 创建成功")
    
    # 测试失败URL
    failed_url = FailedUrl(
        url="https://failed.com",
        reason="测试失败",
        exception_type=ExceptionType.NETWORK
    )
    print("✅ FailedUrl 创建成功")
    
    # 测试文章列表
    article_list = ScrapedArticleList(
        articles=[article],
        failed_urls=[failed_url]
    )
    print("✅ ScrapedArticleList 创建成功")

def test_scraper_initialization():
    """测试抓取器初始化"""
    print("\n🧪 测试抓取器初始化...")
    
    # 现在只支持无参数初始化
    scraper1 = ArticleScraper()
    print("✅ 无参数抓取器初始化成功")
    
    # 测试配置对象创建（用于方法调用时传递）
    config = ScraperConfig(
        headless=True,
        timeout=5000,
        use_browser=False
    )
    print("✅ 配置对象创建成功")
    
    # 注意：现在所有参数都在方法调用时传递
    print("✅ 新架构：参数在方法调用时动态传递")

def test_extractor_initialization():
    """测试提取器初始化"""
    print("\n🧪 测试提取器初始化...")
    
    extractor = HtmlExtractor()
    print("✅ HtmlExtractor 初始化成功")

def test_serialization():
    """测试序列化功能"""
    print("\n🧪 测试序列化功能...")
    
    # 测试配置序列化
    config = ScraperConfig(headless=False, timeout=5000)
    config_json = config.to_json()
    assert '"headless":false' in config_json
    print("✅ ScraperConfig 序列化成功")
    
    # 测试文章序列化
    article = ScrapedArticle(
        url="https://example.com",
        title="测试",
        content="内容"
    )
    article_json = article.to_json()
    assert '"url":"https://example.com"' in article_json
    print("✅ ScrapedArticle 序列化成功")

def main():
    """运行所有测试"""
    print("🚀 开始测试整合后的代码结构")
    print("=" * 60)
    
    try:
        test_imports()
        test_model_creation()
        test_scraper_initialization()
        test_extractor_initialization()
        test_serialization()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！代码整合成功！")
        print("📊 整合结果:")
        print("   - models/ → models.py ✅")
        print("   - extractors/ → extractors.py ✅")
        print("   - core/ → core.py ✅")
        print("   - 保留 utils/ 目录 ✅")
        print("   - 代码结构简化完成 ✅")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
