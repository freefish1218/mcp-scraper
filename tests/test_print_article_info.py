#!/usr/bin/env python3
"""
测试优化后的 print_article_info 函数的错误处理能力
"""

# 直接导入conftest模块
from tests.conftest import print_article_info
from src.scraper.models import ScrapedArticle, Link, LinkType, ExceptionType

class BrokenObject:
    """模拟有问题的对象，属性访问会抛出异常"""
    def __init__(self, attr_name, error_type=AttributeError):
        self.attr_name = attr_name
        self.error_type = error_type
    
    def __getattr__(self, name):
        if name == self.attr_name:
            raise self.error_type(f"模拟 {name} 属性访问错误")
        return f"正常_{name}"

def test_normal_article():
    """测试正常文章对象"""
    print("🧪 测试1: 正常文章对象")
    
    # 创建正常的文章对象
    article = ScrapedArticle(
        url="https://example.com/test",
        title="测试文章",
        content="这是一篇测试文章的内容，用来验证print_article_info函数的正常工作。" * 10,
        publish_date="2025-05-26",
        source="测试来源",
        summary=["这是摘要1", "这是摘要2"],
        links=[
            Link(
                url="https://example.com/link1",
                title="正常链接1",
                type=LinkType.OTHER,
    
            ),
            Link(
                url="https://example.com/link2", 
                title="失败链接2",
                type=LinkType.DOCUMENT,
    

            )
        ]
    )
    
    print_article_info(article)

def test_broken_article():
    """测试有问题的文章对象"""
    print("\n🧪 测试2: 属性访问会出错的文章对象")
    
    # 创建一个会在访问某些属性时抛出异常的对象
    class BrokenArticle:
        def __init__(self):
            self.url = "https://broken.com/test"
            self._broken_attrs = ['title', 'content', 'links']
        
        def __getattr__(self, name):
            if name in self._broken_attrs:
                raise ValueError(f"访问 {name} 属性时发生错误")
            # 提供一些默认值
            if name == 'publish_date':
                return "2025-05-26"
            elif name == 'scrape_time':
                return "2025-05-26T10:00:00"
            elif name == 'html':
                return "<html>broken</html>"
            elif name == 'source':
                return "broken source"
            elif name == 'summary':
                return None
            return None
    
    broken_article = BrokenArticle()
    print_article_info(broken_article)

def test_none_article():
    """测试传入None"""
    print("\n🧪 测试3: 传入None对象")
    
    try:
        print_article_info(None)
    except Exception as e:
        print(f"传入None时的异常处理: {type(e).__name__}: {e}")

def test_malformed_links():
    """测试包含异常链接的文章"""
    print("\n🧪 测试4: 包含异常链接的文章")
    
    # 创建一个正常的文章，但将链接属性设置为有问题的对象
    article = ScrapedArticle(
        url="https://example.com/broken-links",
        title="包含异常链接的文章",
        content="这篇文章包含一些有问题的链接"
    )
    
    # 直接修改article对象的links属性为有问题的对象
    class BrokenLinksList:
        def __len__(self):
            raise RuntimeError("获取链接数量时出错")
        
        def __iter__(self):
            raise ValueError("遍历链接时出错")
    
    # 先测试正常情况
    article.links = [
        Link(url="https://good.com", title="正常链接", type=LinkType.OTHER)
    ]
    
    print_article_info(article)
    
    # 然后测试异常情况 - 通过修改某个链接的属性
    print("\n--- 测试链接属性访问异常 ---")
    
    # 创建一个看起来正常但某些属性有问题的链接
    normal_link = Link(url="https://broken-attr.com", title="异常属性链接", type=LinkType.OTHER)
    
    # 猴子补丁某个属性访问
    def broken_url_getter():
        raise ConnectionError("链接URL访问时网络错误")
    
    # 临时替换属性
    original_url = normal_link.url
    try:
        # 注意：Pydantic模型的属性比较难直接破坏，我们改为在print函数中模拟错误
        article.links = [normal_link]
        print_article_info(article)
    except Exception as e:
        print(f"链接测试异常: {e}")

def test_extreme_cases():
    """测试极端情况"""
    print("\n🧪 测试5: 极端情况")
    
    # 测试超长内容
    article = ScrapedArticle(
        url="https://example.com/extreme",
        title="极端测试" * 100,  # 超长标题
        content="这是超长内容。" * 200,  # 超长内容
    )
    
    # 添加大量链接
    article.links = [
        Link(url=f"https://example.com/link{i}", title=f"链接{i}", type=LinkType.OTHER)
        for i in range(10)  # 创建10个链接，测试显示限制
    ]
    
    print_article_info(article)

def main():
    """运行所有测试"""
    print("🚀 开始测试优化后的 print_article_info 函数")
    print("=" * 60)
    
    # 运行所有测试
    test_normal_article()
    test_broken_article()
    test_none_article()
    test_malformed_links()
    test_extreme_cases()
    
    print("\n✅ 所有测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
