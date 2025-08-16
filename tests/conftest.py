"""
测试配置和辅助函数
"""
from scraper import ScrapedArticle

# 测试用URL列表
TEST_URLS = {
    # 新闻网站
    "news": "https://news.qq.com/rain/a/20250518A066P200",
    # 维基百科文章
    "article": "https://zh.wikipedia.org/wiki/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD",
    # 博客文章
    "blog": "https://www.ruanyifeng.com/blog/2025/04/trae-mcp.html",
    # 简单HTML结构
    "simple": "https://example.com/",
    # 微信文章
    "weixin": "https://mp.weixin.qq.com/s/MSGsvCAmPBJ6G-t3UujBsQ",
    # 知乎文章
    "zhihu": "https://zhuanlan.zhihu.com/p/30341867640",
    # 网易
    "163": "https://www.163.com/news/article/JVRMS1BD000189FH.html?clickfrom=w_yw",
    # 百度文章
    "baidu": "https://baijiahao.baidu.com/s?id=1830024387434208014&wfr=spider&for=pc",
    # BBC文章
    "bbc": "https://www.bbc.com/news/articles/cvgvr4r5d2qo",
    # Forbes文章 (英文)
    "forbes": "https://www.forbes.com/councils/forbestechcouncil/2025/04/21/its-not-all-ai-data-science-innovations-continue-to-shape-business/",
    # RFI文章 (法文)
    "rfi": "https://www.rfi.fr/fr/france/20250501-1er-mai-en-france-des-c%C3%A9l%C3%A9brations-sous-haute-tension-sociale"
}

def get_test_config():
    """提供测试专用的配置"""
    return {
        "headless": True,  # 无头模式
        "timeout": 5000,  # 较长的超时时间
        "max_retries": 3,  # 最大重试次数
        "use_browser": True, # 是否强制使用浏览器抓取
        "referer": "https://www.baidu.com",
        "llm_summary": False, # 是否启用自动总结
    }


def print_article_info(article: ScrapedArticle):
    """打印文章信息方便人工查看，包含错误处理"""
    try:
        print("\n" + "="*50)
        
        # 基本信息打印，单独处理每个字段以避免某个字段出错影响整体
        try:
            print(f"URL: {article.url}")
        except Exception as e:
            print(f"URL: [获取失败: {type(e).__name__}: {e}]")
        
        try:
            print(f"发布时间: {article.publish_date}")
        except Exception as e:
            print(f"发布时间: [获取失败: {type(e).__name__}: {e}]")
        
        try:
            print(f"标题: {article.title}")
        except Exception as e:
            print(f"标题: [获取失败: {type(e).__name__}: {e}]")
        
        try:
            links_count = len(article.links) if hasattr(article, 'links') and article.links else 0
            print(f"链接数量: {links_count}")
        except Exception as e:
            print(f"链接数量: [获取失败: {type(e).__name__}: {e}]")
        
        try:
            print(f"抓取时间: {article.scrape_time}")
        except Exception as e:
            print(f"抓取时间: [获取失败: {type(e).__name__}: {e}]")
        
        try:
            html_size = len(article.html) if hasattr(article, 'html') and article.html else 0
            print(f"HTML大小: {html_size}字节")
        except Exception as e:
            print(f"HTML大小: [获取失败: {type(e).__name__}: {e}]")
        
        # 内容预览
        try:
            print("\n内容:")
            if hasattr(article, 'content') and article.content:
                content_preview = article.content[:500] + "..." if len(article.content) > 500 else article.content
                print(content_preview)
            else:
                print("[无内容]")
        except Exception as e:
            print(f"[内容获取失败: {type(e).__name__}: {e}]")

        # 来源信息
        try:
            source_info = getattr(article, 'source', None)
            print(f"\n来源: {source_info}")
        except Exception as e:
            print(f"\n来源: [获取失败: {type(e).__name__}: {e}]")

        # 摘要信息
        try:
            summary_info = getattr(article, 'summary', None)
            print(f"\n摘要: {summary_info}")
        except Exception as e:
            print(f"\n摘要: [获取失败: {type(e).__name__}: {e}]")

        # 链接详细信息
        try:
            links = getattr(article, 'links', [])
            # 筛选出文档类型的链接
            links = [link for link in links if hasattr(link, 'type') and link.type == 'document']

            if links:
                print(f"\n文档链接详情:")
                for i, link in enumerate(links[:10]):  # 只显示前10个链接
                    try:
                        link_url = getattr(link, 'url', '[无URL]')
                        link_title = getattr(link, 'title', '[无标题]')
                        link_type = getattr(link, 'type', '[无类型]')
                        
                        print(f"  {i+1}. {link_title}")
                        print(f"     URL: {link_url}")
                        print(f"     类型: {link_type}")
                                                    
                    except Exception as e:
                        print(f"  {i+1}. [链接解析失败: {type(e).__name__}: {e}]")
                
                if len(links) > 10:
                    print(f"  ... 还有 {len(links) - 10} 个链接")
        except Exception as e:
            print(f"\n链接详情: [获取失败: {type(e).__name__}: {e}]")

        print("="*50)
        
    except Exception as e:
        # 如果整个函数都出错了，至少要显示错误信息
        print(f"\n❌ print_article_info 函数执行失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print(f"   文章对象类型: {type(article)}")
        
        # 尝试至少显示基本信息
        try:
            if hasattr(article, 'url'):
                print(f"   URL: {article.url}")
        except:
            pass
        
        print("="*50)
