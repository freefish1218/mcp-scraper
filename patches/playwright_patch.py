"""
Playwright Docker 沙盒补丁模块
解决Docker环境中Chrome沙盒问题
"""

import os
from typing import List, Optional
from scraper.utils.logger import get_logger

logger = get_logger('patches.playwright', level="INFO")


def get_docker_chrome_args() -> List[str]:
    """
    获取Docker环境中Chrome的启动参数
    
    Returns:
        List[str]: Chrome启动参数列表
    """
    return [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        # 以下两参数会导致: Canvas has no webgl context
        # '--disable-gpu',
        # '--disable-features=VizDisplayCompositor',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-background-networking',
        '--disable-default-apps',
        '--disable-extensions',
        '--disable-sync',
        '--disable-translate',
        '--hide-scrollbars',
        '--mute-audio',
        '--no-first-run',
        '--disable-breakpad',
        '--disable-infobars',
        '--window-position=0,0',
        '--ignore-certificate-errors',
        '--ignore-ssl-errors',
        '--ignore-certificate-errors-spki-list',
        '--disable-web-security',
    ]


def is_docker_environment() -> bool:
    """
    检测是否在Docker容器环境中运行
    
    Returns:
        bool: 如果在Docker环境中返回True
    """
    return (
        os.path.exists('/.dockerenv') or 
        os.getenv('RUNNING_IN_DOCKER') == 'true' or
        os.getenv('DOCKER_CONTAINER') == 'true'
    )


def apply_playwright_patch() -> None:
    """
    应用Playwright Docker补丁
    """
    try:
        # if not is_docker_environment():
        #     logger.info("非Docker环境，跳过Playwright沙盒补丁")
        #     return
        
        # 设置环境变量确保Playwright使用正确的Chrome参数
        chrome_args = get_docker_chrome_args()
        
        # 为Playwright设置环境变量
        os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = '/opt/google/chrome/chrome'
        os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
        
        # 尝试直接修改Playwright的launch方法
        try:
            from playwright.async_api import Browser, BrowserType
            
            # 保存原始的launch方法
            if not hasattr(BrowserType, '_original_launch'):
                BrowserType._original_launch = BrowserType.launch
            
            # 创建补丁版本的launch方法
            async def patched_launch(self, **kwargs):
                """带Docker沙盒解决方案的launch补丁"""
                # 如果没有明确指定args，添加Docker兼容参数
                if 'args' not in kwargs:
                    kwargs['args'] = chrome_args
                else:
                    # 如果已有args，合并我们的参数
                    existing_args = kwargs.get('args', [])
                    # 确保 existing_args 是列表类型，防止元组错误
                    if not isinstance(existing_args, list):
                        existing_args = list(existing_args) if existing_args else []
                    # 只添加不存在的参数
                    for arg in chrome_args:
                        if arg not in existing_args:
                            existing_args.append(arg)
                    kwargs['args'] = existing_args
                
                logger.debug(f"Playwright launch args: {kwargs.get('args', [])[:5]}...")
                return await self._original_launch(**kwargs)
            
            # 替换launch方法
            BrowserType.launch = patched_launch
            logger.info("成功应用Playwright BrowserType.launch Docker补丁")
            
        except ImportError:
            logger.warning("无法导入Playwright模块，跳过launch方法补丁")
        
        logger.info(f"已应用Playwright Docker补丁，Chrome参数数量: {len(chrome_args)}")
        logger.debug(f"Chrome启动参数: {' '.join(chrome_args)[:100]}...")
        
    except Exception as e:
        logger.error(f"应用Playwright补丁时发生错误: {e}", exc_info=True)
