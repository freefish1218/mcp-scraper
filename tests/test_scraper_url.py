import asyncio
from scraper import ArticleScraper
from conftest import get_test_config, print_article_info


async def test_scraper():
    """测试抓取器的基本功能"""
    print("\n[测试] 抓取器基本功能")
    
    # 创建抓取器
    # 创建抓取器（现在使用无参数初始化）
    scraper = ArticleScraper()
    
    # 获取测试配置（用于方法调用时传递）
    test_config = get_test_config()
    
    # 准备测试URL

    # 标题问题
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202412/t20241203_23773371.htm'

    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202407/t20240726_22732680.htm'

    # 下载附件问题
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202504/t20250422_24477199.htm'
    # test_url = 'http://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202505/t20250516_24610273.htm' # Zip文件

    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202505/t20250516_24609774.htm' # 两文档有重复
    # test_url = 'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250515_24603632.htm'
    # test_url = 'http://www.ccgp.gov.cn/cggg/dfgg/cjgg/202505/t20250521_24634031.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/jzxcs/202505/t20250515_24598330.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250513_24590024.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/cjgg/202505/t20250513_24590591.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gzgg/202505/t20250514_24592507.htm'
    # test_url = 'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250521_24632543.htm'
    # test_url = 'http://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250522_24640547.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/zygg/zbgg/202505/t20250521_24633895.htm'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250520_24628991.htm'

    # docx, 浙江 oss (易 403) - 结果应只有1个文档
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250520_24628992.htm'

    # 正常pdf
    # test_url = 'https://gpx.ccgp-sichuan.gov.cn/gpx-bid-file/ZF_JGBM_000008/zone/2024/12/15/project/gpx-template/8a69ccf196e4cd520196e7bf99175922.pdf?accessCode=d797e701e1318c7b2599260f77c329e0'
    # test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250519_24620822.htm'

    # 含 doc 与 图片pdf
    test_url = 'https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250516_24612662.htm'
    # test_url = 'https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1023FP/339900/10007868109/20255/93f498f8-a17f-4668-b1e7-b2258edd93eb.doc'
    # test_url = 'https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1024FPA/339900/10007868109/20255/bdc99034-111d-49ce-8048-f11c2529e334.pdf'

    # test_url = 'https://example.com/'
    # test_url = 'https://zh.wikipedia.org/wiki/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD'
    # test_url = 'https://leetarxiv.substack.com/p/counting-integer-compositions'
    # test_url = 'https://www.163.com/news/article/JVN4SLGF0001899O.html'
    # test_url = 'https://www.bbc.com/news/articles/cvgvr4r5d2qo'
    # test_url = 'https://mp.weixin.qq.com/s/GEb1E-cRKi3awGZSwG3Ngg'
    # test_url = 'https://mp.weixin.qq.com/s/MSGsvCAmPBJ6G-t3UujBsQ'
    # test_url = 'https://www.bbc.com/news'
    # test_url = 'https://sergii.tatarenkov.name/keyclu/support/'
    # test_url = 'https://formulae.brew.sh/cask/shortcutdetective'
    # test_url = 'https://news.ycombinator.com/'
    # test_url = 'https://newspaper4k.readthedocs.io/en/latest/user_guide/api_reference.html#source'
    # test_url = 'https://www.msn.com/en-us/technology/artificial-intelligence/missile-developments-in-the-ai-era/ar-AA1BgZvK'
    
    print(f"抓取页面: {test_url}")
    
    try:
        # 抓取页面（传递配置参数）
        article = await scraper.scrape(
            url=test_url,
            **test_config  # 展开测试配置参数
        )

        if not article:
            print("x 抓取失败，未抓取到内容")

        print_article_info(article)
        
        # 验证抓取结果
        assert article.title, "标题为空"
        assert len(article.content) > 0, "内容为空"
        
        print("✓ 抓取成功，所有验证通过")
    except Exception as e:
        print(f"网页抓取失败: {type(e).__name__}")
        print(f"错误信息: {str(e)}")


if __name__ == "__main__":    
    # 运行测试
    asyncio.run(test_scraper())
