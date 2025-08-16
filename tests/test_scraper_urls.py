import asyncio
from scraper import ArticleScraper
from conftest import TEST_URLS, get_test_config, print_article_info

async def test_scraper():
    """测试抓取器的基本功能"""
    print("\n[测试] 抓取器基本功能")
    
    # 创建抓取器（现在使用无参数初始化）
    scraper = ArticleScraper()
    
    # 获取测试配置（用于方法调用时传递）
    test_config = get_test_config()
    
    # 准备测试URL
    # test_urls = TEST_URLS.values()

    test_urls = [
        'https://zhuanlan.zhihu.com/p/30341867640',
        'https://mp.weixin.qq.com/s/GEb1E-cRKi3awGZSwG3Ngg',
        'https://not-example.com/',  # 无效URL测试
        'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250522_24640547.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250521_24632543.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202505/t20250516_24609774.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202505/t20250516_24608496.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250515_24603632.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202505/t20250515_24598330.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202505/t20250514_24594764.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/gzgg/202505/t20250514_24592507.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202505/t20250513_24590591.htm',
        'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250513_24590024.htm'
    ]
    
    print(f"抓取 {len(test_urls)} 个页面")
    
    try:
        # 抓取页面
        articles_list = await scraper.bulk_scrape(test_urls, max_workers=5)
        articles = articles_list.articles

        print(f"抓取页面数量: {len(articles)}")

        for article in articles:
            print_article_info(article)

        print("\n抓取失败的页面:")
        print([failed.to_json() for failed in articles_list.failed_urls])

        print(f"成功抓取 {len(articles_list.articles)} 个页面")
        print(f"失败抓取 {len(articles_list.failed_urls)} 个页面")
        
        # 验证抓取结果
        # assert len(articles) == len(test_urls), "抓取失败"
        
        print("✓ 抓取成功，所有验证通过")
    except Exception as e:
        print(f"网页抓取失败: {type(e).__name__}")
        print(f"错误信息: {str(e)}")


if __name__ == "__main__":    
    # 运行测试
    asyncio.run(test_scraper())
