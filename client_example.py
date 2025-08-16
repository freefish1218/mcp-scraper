"""
MCP-Scraper 使用示例
演示如何使用 MCP 服务器进行网页内容抓取和处理
"""

import json
import asyncio
import argparse
import textwrap
from typing import Dict, Any, List, Union
from datetime import datetime

# 导入必要的模块
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class MCPScraperClient:
    """MCP-Scraper 客户端封装类"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:3001/mcp",
    ):
        """
        初始化 MCP-Scraper 客户端
        
        Args:
            base_url: 服务器地址
        """
        self.base_url = base_url
        
        # 配置客户端
        self._setup_client()
        
    def _setup_client(self):
        """配置客户端连接"""
        # 显式 StreamableHttp 传输
        transport = StreamableHttpTransport(
            url=self.base_url
        )
        self.client = Client(transport)
    
    async def connect(self):
        """连接到服务器"""
        return self.client
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None):
        """
        调用工具函数
        """
        async with self.client as client:
            return await client.call_tool(tool_name, arguments)
        
    
    async def list_tools(self):
        """
        列出可用工具
        """
        async with self.client as client:
            return await client.list_tools()


# 格式化输出函数
def print_header(title: str):
    """打印格式化标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)

def print_json(data: Union[Dict, List]):
    """格式化打印JSON数据"""
    print(json.dumps(data, ensure_ascii=False, indent=2))

def format_content(content: str, max_length: int = 100) -> str:
    """格式化长文本内容"""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


async def main(args):
    """运行所有示例"""
    print_header(f"MCP-Scraper 客户端示例 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 创建客户端
    base_url = f"http://localhost:{args.port}/mcp"
    client = MCPScraperClient(base_url)
    
    try:
        # 示例: 获取服务器信息
        print_header("示例: 获取服务器信息")
        print(f"可用工具: {await client.list_tools()}")
        
        # 示例: 抓取单个 URL
        print_header("示例: 抓取单个 URL")
        
        url_to_scrape = args.url or "https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250515_24603632.htm"
        print(f"正在抓取 URL: {url_to_scrape}")
        
        try:
            start_time = datetime.now()

            # FastMCP: call_tool 返回一个内容对象的列表 (通常是 TextContent 对象)
            article_response = await client.call_tool("scrape", {
                "url": url_to_scrape,
                "use_browser": True,
                "llm_summary": False
            })
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"article_response type: {type(article_response)}")

            # 确保响应不为空
            if not article_response or not isinstance(article_response, list) or len(article_response) == 0:
                raise ValueError("无效的响应格式：响应为空或不是列表类型")

            # 获取第一个内容对象（通常是 TextContent）
            text_content = article_response[0]

            # print(text_content)

            # 确保它具有 text 属性
            if not hasattr(text_content, 'text') or not text_content.text:
                raise ValueError("无效的响应格式：内容对象没有 text 属性或 text 为空")
            
            # 解析 JSON 字符串为字典
            try:
                article = json.loads(text_content.text)
            except json.JSONDecodeError:
                raise ValueError(f"无法解析响应为 JSON: {text_content.text[:100]}...")

            print(f"✓ 抓取成功 (耗时: {duration:.2f}秒)")
            print(f"抓取时间: {article.get('scrape_time', 'N/A')}")
            print(f"标题: {article.get('title', 'N/A')}")
            print(f"内容长度: {len(article.get('content', ''))}")
            print("内容预览:")
            content_preview = article.get('content', '')[:200]
            for line in textwrap.wrap(content_preview, width=70):
                print(f"  {line}")
            print(f"图片数: {len(article.get('images', []))}")
            print(f"链接数: {len(article.get('links', []))}")
            print(f"总结: {article.get('summary', 'N/A')}")
            
        except Exception as e:
            print(f"× 抓取失败: {str(e)}")
        

        # return
        
        # 示例: 批量抓取多个 URL
        print_header("示例: 批量抓取")
        
        urls = [
            "https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202505/t20250519_24620822.htm",
            "https://news.ycombinator.com/",
            "https://www.bbc.com/news",
            "https://www.npr.org/sections/news/"
        ]
        
        if args.bulk_urls:
            try:
                urls = args.bulk_urls.split(',')
            except:
                print("无法解析批量URL，使用默认URL")
                
        print(f"批量抓取 {len(urls)} 个 URL:")
        for url in urls:
            print(f"- {url}")
        
        try:                
            # 批量抓取
            start_time = datetime.now()
            print("开始批量抓取...")
            # FastMCP: call_tool 返回一个内容对象的列表 (通常是 TextContent 对象)
            articles_response = await client.call_tool("bulk_scrape", {
                "urls": urls,
                "llm_summary": False
            })
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 确保响应不为空
            if not articles_response or not isinstance(articles_response, list) or len(articles_response) == 0:
                raise ValueError("无效的响应格式：响应为空或不是列表类型")

            # 获取第一个内容对象（通常是 TextContent）
            text_content = articles_response[0]
            
            # 确保它具有 text 属性
            if not hasattr(text_content, 'text') or not text_content.text:
                raise ValueError("无效的响应格式：内容对象没有 text 属性或 text 为空")
            
            # 解析 JSON 字符串为字典
            try:
                response_data = json.loads(text_content.text)
                
                # 检查响应格式，服务器返回的是 ScrapedArticleList 对象
                if isinstance(response_data, dict) and 'articles' in response_data:
                    articles = response_data['articles']
                    failed_urls = response_data.get('failed_urls', [])
                    
                    # 显示失败的URL信息
                    if failed_urls:
                        print(f"警告: {len(failed_urls)} 个URL抓取失败:")
                        for failed in failed_urls:
                            print(f"  - {failed.get('url', 'N/A')}: {failed.get('reason', 'N/A')}")
                elif isinstance(response_data, list):
                    # 兼容旧格式
                    articles = response_data
                else:
                    raise ValueError(f"无效的响应格式：期望包含 'articles' 字段的对象或数组，实际收到: {type(response_data)}")
                    
                if not isinstance(articles, list):
                    raise ValueError(f"无效的文章数据格式：期望数组，实际收到: {type(articles)}")
            except json.JSONDecodeError:
                raise ValueError(f"无法解析响应为 JSON: {text_content.text[:100]}...")
            
            print(f"✓ 批量抓取完成 (耗时: {duration:.2f}秒)")
            
            # 显示结果
            for i, article in enumerate(articles):
                print(f"{i+1}. {article.get('title', 'N/A')}")
                print(f"   URL: {article.get('url', 'N/A')}")
                print(f"   抓取时间: {article.get('scrape_time', 'N/A')}")
                print(f"   内容长度: {len(article.get('content', ''))}")
                print(f"   图片数: {len(article.get('images', []))}")
                print(f"   链接数: {len(article.get('links', []))}")    
                print(f"   总结: {article.get('summary', 'N/A')}")
                print("")
        except Exception as e:
            print(f"× 批量抓取失败: {str(e)}")
    
    except Exception as e:
        print(f"运行示例时出错: {str(e)}")
    
    print_header("示例运行完成")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="MCP-Scraper 客户端示例")
    
    parser.add_argument("--port", "-p", type=int, default="3001", help="服务器端口")
    parser.add_argument("--url", type=str, 
                        help="要抓取的单个URL")
    parser.add_argument("--bulk-urls", type=str,
                        help="批量抓取的URL，用逗号分隔")
                        
    return parser.parse_args()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 运行异步主函数
    asyncio.run(main(args))
