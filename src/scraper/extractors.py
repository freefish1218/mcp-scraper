"""
内容提取模块

整合了所有的内容提取器，包括基础提取器、日期提取器、标题提取器、链接提取器和HTML提取器
提供从HTML中提取结构化内容的功能
"""

import urllib.parse
from typing import Any, Optional, List, Dict
from htmldate import find_date
from scrapling.engines.toolbelt import Response
from scrapling.engines.toolbelt.custom import Response as CustomResponse

from scraper.models import Link, LinkType, ScrapedArticle
from scraper.utils.files import is_doc_url
from scraper.utils.url import normalize_url, is_image_url, generate_title_from_url, get_ext_by_url
from scraper.utils.network import handle_http_errors, NetworkError
from scraper.utils.logger import get_logger


# ============================================================================
# 基础提取器
# ============================================================================

class BaseExtractor:
    """
    提取器基类
    
    所有特定类型的提取器都应继承此基类，实现共享功能
    """
    
    def __init__(self):
        """初始化提取器基类"""
        # 创建日志记录器
        self.logger = get_logger(self.__class__.__name__)
    
    def extract(self, *args, **kwargs) -> Any:
        """
        提取方法（需要由子类实现）
        
        Returns:
            提取结果，具体类型由子类决定
            
        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("子类必须实现extract方法")


# ============================================================================
# 日期提取器
# ============================================================================

class DateExtractor(BaseExtractor):
    """
    日期提取器
    
    负责从HTML内容中提取文章发布日期
    """
    
    def extract(self, html_content: str) -> Optional[str]:
        """
        从HTML内容中提取发布日期
        
        Args:
            html_content: HTML内容
            
        Returns:
            Optional[str]: 提取的发布日期，如果提取失败则返回None
        """
        try:
            return find_date(html_content)
        except Exception as e:
            self.logger.error(f"提取发布日期失败: {e}")
            return None


# ============================================================================
# 标题提取器
# ============================================================================

class TitleExtractor(BaseExtractor):
    """
    标题提取器
    
    负责从HTML内容中提取文章标题
    """
    
    def extract(self, page: Response, title_min_length: int = 5) -> str:
        """
        从HTML内容中提取标题
        
        Args:
            page: Response对象
            title_min_length: 标题最小长度
            
        Returns:
            str: 提取的标题，如果提取失败则返回空字符串
        """
        # 先取title标签
        title = page.css_first('title::text')

        # 如果title标签不符合要求，再取h1标签
        if not title or len(title.strip()) < title_min_length:
            title = page.css_first('h1::text')

        # 如果h1标签不符合要求，再取h1标签的子元素
        if not title or len(title.strip()) < title_min_length:
            title = page.css_first('h1')
            if title:
                title = title.get_all_text().clean()  # 针对子元素

        return title or ""


# ============================================================================
# 链接提取器
# ============================================================================

# 创建工具模块的logger
logger = get_logger("extractor.link")


def extract_links(
    page: CustomResponse,
    base_url: str,
) -> List[Link]:
    """
    从HTML内容中提取链接，包括 a 标签的 href 和 img 标签的 src
    
    Args:
        page: Response对象
        base_url: 页面原始URL
        
    Returns:
        List[Link]: 提取的链接列表
    """
    try:
        # 提取链接
        a_links = _extract_a_links(page)
        img_links = _extract_img_links(page)
        all_links = a_links + img_links
        
        # 过滤无效链接
        filtered_links = _filter_invalid_links(all_links)
        
        # 移除重复链接 - 使用URL作为键
        unique_urls = {}
        for link in filtered_links:
            unique_urls[link['url']] = link
        unique_links = list(unique_urls.values())
        
        # 处理URLs和标题
        processed_links = _convert_to_absolute_urls(unique_links, base_url)

        # 分类链接
        return _categorize_links(processed_links, img_links)
    except Exception as e:
        logger.error(f"提取链接失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def _extract_a_links(page: CustomResponse) -> List[Dict[str, str]]:
    """从页面中提取所有 a 标签的链接"""
    a_tags = page.find_all('a')
    a_links = []
    
    for link in a_tags:
        href = link.attrib.get('href')
        if not href:  # 跳过没有 href 属性的链接
            continue
        title = link.text.strip() or link.attrib.get('title') or ""
        
        # 标准化URL
        url = normalize_url(href)
        # 规范化title
        title = title.lower().strip()
        a_links.append({"url": url, "title": title})
    
    return a_links


def _extract_img_links(page: CustomResponse) -> List[Dict[str, str]]:
    """从页面中提取所有 img 标签的链接，按照优先级处理不同图片源属性"""
    img_tags = page.find_all('img')
    img_links = []
    
    for img in img_tags:
        # 获取图片标题属性
        alt_text = img.attrib.get('alt')
        title_text = img.attrib.get('title')
        title = alt_text or title_text or ""  # 优先使用 alt 文本作为标题
        
        url = None  # 初始化图片URL
        
        # 1. 先检查 src 属性（最高优先级）
        if img.attrib.get('src'):
            url = img.attrib.get('src')
            
        # 2. 如果没有 src，检查 data-src 属性（延迟加载常用）
        elif img.attrib.get('data-src'):
            url = img.attrib.get('data-src')
            
        # 3. 如果前两个属性都没有，再检查 srcset 属性
        elif img.attrib.get('srcset'):
            srcset = img.attrib.get('srcset')
            # 从 srcset 中取最后一个URL（通常是最高分辨率）
            srcset_entries = [entry.strip() for entry in srcset.split(',')]
            if srcset_entries:  # 如果有条目
                # 取最后一个条目的URL部分
                last_entry = srcset_entries[-1]
                url_part = last_entry.split(' ')[0].strip() if ' ' in last_entry else last_entry
                url = url_part
                
        # 4. 最后尝试 data-srcset 属性
        elif img.attrib.get('data-srcset'):
            data_srcset = img.attrib.get('data-srcset')
            # 从 data-srcset 中取最后一个URL
            data_srcset_entries = [entry.strip() for entry in data_srcset.split(',')]
            if data_srcset_entries:
                last_entry = data_srcset_entries[-1]
                url_part = last_entry.split(' ')[0].strip() if ' ' in last_entry else last_entry
                url = url_part
        
        # 如果找到了URL，添加到链接列表
        if url:
            # 排除无效的图片名称
            invalid_image_names = ['placeholder']
            image_name = url.split('/')[-1].split('.')[0]
            if any(name in image_name for name in invalid_image_names):
                continue

            # 标准化URL
            url = normalize_url(url)
            # 规范化title
            title = title.lower().strip()
            img_links.append({"url": url, "title": title})
    
    return img_links


def _filter_invalid_links(links: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """过滤掉无效的链接"""
    filter_startswith = [
        '#',
        'javascript:', 'mailto:', 'tel:',
        'data:', 'blob:',
        'whatsapp:', 'fb-messenger:',
        'tg:', 'viber:', 'skype:', 'slack:',
        'weixin:', 'wechat:',
        'chrome:', 'edge:', 'opera:', 'safari:', 'firefox:',
    ]

    filter_endswith = [
        '.iso', '.img', '.bin', '.dmg', '.pkg', '.exe', '.msi', '.deb', '.rpm', '.app', '.ipa', '.apk',
        '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
    ]

    return [
        link for link in links 
        if link['url'] and link['url'] != '/' \
            and not any(link['url'].startswith(start) for start in filter_startswith) \
            and not any(link['url'].endswith(end) for end in filter_endswith)
    ]


def _convert_to_absolute_urls(links: List[Dict[str, str]], base_url: str) -> List[Dict[str, str]]:
    """将相对URL转换为绝对URL, 并处理空标题"""
    result_links = []
    
    for link in links:
        url = link['url']
        title = link['title']
        
        # 为空标题生成标题
        if not title or title == 'None':
            title = generate_title_from_url(url)
        
        # 将相对URL转换为绝对URL
        if url.startswith('/'):
            url = urllib.parse.urljoin(base_url, url)
            logger.debug(f"将相对URL {link['url']} 转换为绝对URL {url}")
                
        result_links.append({"title": title, "url": url})
    
    return result_links


def _categorize_links(
    links: List[Dict[str, str]],
    img_links: List[Dict[str, str]],
) -> List[Link]:
    """将链接分类为图片链接、文档链接和其他链接"""
    final_links = []

    img_urls = [img_link['url'] for img_link in img_links]
    
    for link in links:
        # 处理网页链接
        ext = get_ext_by_url(link['url'])
        if ext in ['.html', '.htm', '.shtml']:
            final_links.append(
                Link(
                    url=link['url'], 
                    title=link['title'], 
                    type=LinkType.OTHER
                )
            )

        # 处理图片链接
        elif link['url'] in img_urls:
            final_links.append(
                Link(
                    url=link['url'], 
                    title=link['title'], 
                    type=LinkType.IMAGE
                )
            )
        elif is_image_url(link['url']):
            final_links.append(
                Link(
                    url=link['url'], 
                    title=link['title'], 
                    type=LinkType.IMAGE
                )
            )

        # 处理文档链接
        elif is_doc_url(link['url']):
            final_links.append(
                Link(
                    url=link['url'], 
                    title=link['title'], 
                    type=LinkType.DOCUMENT
                )
            )

        # 其他链接
        else:
            final_links.append(
                Link(
                    url=link['url'], 
                    title=link['title'], 
                    type=LinkType.OTHER
                )
            )
    
    return final_links


class LinkExtractor(BaseExtractor):
    """
    链接提取器
    
    负责从HTML内容中提取链接
    """
    
    def __init__(self):
        """
        初始化链接提取器
        """
        super().__init__()
        # 初始化日志记录器
        self.logger = get_logger("extractor.link")
    
    def extract(self, page: Response, base_url: str) -> List[Link]:
        """
        从HTML内容中提取链接
        
        Args:
            page: Response对象
            base_url: 基础URL，用于解析相对路径
            
        Returns:
            List[Link]: 提取的链接列表
        """
        try:
            return extract_links(page, base_url=base_url)
        except Exception as e:
            self.logger.error(f"提取链接失败: {e}")
            return []


# ============================================================================
# HTML提取器（主提取器）
# ============================================================================

class HtmlExtractor(BaseExtractor):
    """
    HTML提取器
    
    负责从HTML内容中提取结构化内容，包括标题、日期、正文和链接
    集成了多个专用提取器
    """
    
    def __init__(self):
        """初始化HTML提取器"""
        super().__init__()
        # 初始化子提取器
        self.date_extractor = DateExtractor()
        self.title_extractor = TitleExtractor()
        self.link_extractor = LinkExtractor()
    
    def _extract_content(self, page: Response, min_content_length: int = 100) -> str:
        """
        提取页面正文内容
        
        Args:
            page: Response对象
            min_content_length: 最小内容长度
            
        Returns:
            str: 提取的正文内容
        """
        # 忽略的标签
        ignore_tags = (
            # 脚本和样式
            'script', 'style', 'noscript',
            # 页眉相关 (包括标签和类)
            'header', '*[class*="header"]', '[role="banner"]',
            # 页脚相关
            'footer', '*[class*="footer"]', '[role="contentinfo"]',
            # 导航相关
            'nav', '*[class="nav-top"]', '*[class="nav-bottom"]', '*[class="main-menu"]', '[role="navigation"]',
            # 侧边栏相关
            'aside', '*[class*="sidebar"]',
            # 面包屑和其他导航元素
            '*[class*="breadcrumb"]',
            # 相关推荐
            '*[class*="post_recommends"]', '*[class*="post_side"]', '*[class*="post_related"]',
            # 广告和其他无关内容
            '*[class*="advertisement"]', '*[class*="banner"]', '*[class*="ads"]'
        )
        
        # 提取正文内容
        return page.get_all_text(ignore_tags=ignore_tags).clean()
    
    @handle_http_errors
    def extract(
        self,
        url: str,
        page: Response,
        min_content_length: int = 100,
    ) -> Optional[ScrapedArticle]:
        """
        从HTML内容中提取结构化内容
        
        Args:
            url: 文章URL
            page: Response对象
            min_content_length: 最小内容长度
            
        Returns:
            Optional[ScrapedArticle]: 提取的文章数据，如果提取失败则返回None
            
        Raises:
            NetworkError: 当发生网络连接问题时抛出
        """
        try:
            # 提取发布日期
            publish_date = self.date_extractor.extract(page.html_content) or ""

            # 提取标题
            title = self.title_extractor.extract(page, title_min_length=5)

            # 提取正文内容
            content = self._extract_content(page, min_content_length)

            # 检查提取质量
            if not content or len(content) < min_content_length:
                return None

            if title:
                title = title.strip()
                # 从正文去除标题
                content = content.replace(title, '').strip()

            # 提取链接
            links = self.link_extractor.extract(page, base_url=url)

            # 构建提取的文章数据
            return ScrapedArticle(
                url=url,
                publish_date=publish_date,
                title=title,
                content=content,
                links=links,
                html=page.html_content,
            )
        except NetworkError:
            # 网络异常已被装饰器处理并转换，直接向上抛出
            self.logger.error(f"信息提取失败: {url}, 网络连接错误")
            raise
        except Exception as e:
            self.logger.warning(f"信息提取失败: {url}, 错误: {str(e)}")
            return None
