import asyncio
import os
from scraper import ScraperConfig, ArticleScraper
from playwright.async_api import Page


async def test_browser_stealth():
    """测试浏览器抓取反反爬能力"""
    print("\n[测试] 浏览器抓取反反爬能力")
    
    # 确保screenshots目录存在
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # 测试网站列表
    test_sites = [
        'https://bot.sannysoft.com',
        'https://arh.antoinevastel.com/bots/areyouheadless',
        'https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html',
        'https://antoinevastel.com/bots/',
        'https://recaptcha-demo.appspot.com/recaptcha-v3-request-scores.php'
    ]    


    async def shot_page(page: Page):
        # 截图保存结果
        screenshot_name = f"stealth_test_{site.split('//')[1].split('/')[0]}.png"
        screenshot_path = os.path.join(screenshots_dir, screenshot_name)
        await page.screenshot(path=screenshot_path)
        print(f"截图保存至: {screenshot_path}")
        return page
    
    # 初始化Scraper配置
    config = ScraperConfig(
        use_browser=True,
    )

    # 创建ArticleScraper实例
    # 创建抓取器（现在使用无参数初始化）
    scraper = ArticleScraper()

    for site in test_sites:
        print(f"\n测试站点: {site}")

        # 使用 WebFetcherFactory 直接调用
        from scraper.core import WebFetcherFactory
        
        # 创建配置用于这次调用
        temp_config = ScraperConfig(use_browser=True)
        
        page = await WebFetcherFactory._fetch_use_browser(
            url=site,
            config=temp_config,
            page_action=shot_page
        )

        # 提取页面内容，检查是否有机器人检测提示
        content = page.get_all_text().clean()
        
        # 分析是否被检测为机器人的关键词
        bot_detection_keywords = [
            "bot detected", 
            "automation detected",
            "headless detected",
            "automated browser",
            "automated test"
        ]
        
        detected = False
        for keyword in bot_detection_keywords:
            if keyword.lower() in content.lower():
                print(f"⚠️ 检测到关键词: '{keyword}'")
                detected = True
        
        if not detected:
            print("✓ 未检测到明显的反爬识别")


if __name__ == "__main__":    
    # 运行测试
    asyncio.run(test_browser_stealth())
