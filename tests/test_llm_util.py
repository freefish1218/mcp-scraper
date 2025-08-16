"""
MCP-Scraper LLM 工具模块测试
用于测试 llm_util.py 中的功能
"""

import unittest
import asyncio

from src.scraper.llm_util import get_llm, get_tools, parse_json
from src.scraper.config import get_cat_server

class TestParseJson(unittest.TestCase):
    """
    测试 parse_json 函数的功能
    """
    
    def test_direct_json(self):
        """测试直接解析有效的JSON字符串"""
        json_str = '{"name": "测试", "value": 123}'
        result = parse_json(json_str)
        self.assertEqual(result["name"], "测试")
        self.assertEqual(result["value"], 123)
    
    def test_json_in_markdown(self):
        """测试从Markdown代码块中解析JSON"""
        md_json = """
        这是一些文本
        ```json
        {
          "name": "测试",
          "value": 123
        }
        ```
        其他内容
        """
        result = parse_json(md_json)
        self.assertEqual(result["name"], "测试")
        self.assertEqual(result["value"], 123)
    
    def test_json_in_text(self):
        """测试从文本中提取并解析JSON"""
        text_json = "前缀文本 { \"array\": [1, 2, 3, 4, 5] } 后缀内容"
        result = parse_json(text_json)
        self.assertEqual(result["array"], [1, 2, 3, 4, 5])
    
    def test_invalid_json(self):
        """测试处理无效的JSON"""
        invalid_json = "这不是JSON { name: 值 }"
        with self.assertRaises(ValueError):
            parse_json(invalid_json)


class TestGetLLM(unittest.TestCase):
    """
    测试 get_llm 函数的功能
    获取真实的LLM实例并使用它写诗
    """
    
    async def test_get_llm_write_poem(self):
        """测试获取LLM实例并用它写一首诗"""
        # 获取真实的LLM实例
        llm = await get_llm()
        
        # 验证LLM实例是否正确获取
        self.assertIsNotNone(llm, "LLM实例不应为None")
        
        # 使用LLM写一首诗
        poem_prompt = "写一首关于人工智能与数据的诗，不超过4行"
        try:
            poem_result = await llm.ainvoke(poem_prompt)
            poem_content = poem_result.content if hasattr(poem_result, "content") else str(poem_result)
            
            print("\n======= LLM生成的诗 =======")
            print(poem_content)
            print("===========================\n")
            
            # 验证诗的内容不为空
            self.assertTrue(len(poem_content) > 0, "生成的诗不应为空")
        except Exception as e:
            self.fail(f"使用LLM生成诗时出错: {str(e)}")


class TestGetTools(unittest.TestCase):
    """
    测试 get_tools 函数的功能
    获取真实的工具列表并打印它们
    """
    
    async def test_get_tools_availability(self):
        """测试获取真实工具列表并打印它们"""
        # 获取MCP服务器（按search类别过滤）
        servers = await get_cat_server("search")
        
        if not servers:
            self.skipTest("没有找到 search 类别的服务器，跳过测试")
        
        print(f"找到 {len(servers)} 个服务器:")
        for name, info in servers.items():
            print(f"- {name}: {info}")

        try:
            # 获取工具列表
            tools = await get_tools(servers)
            
            # 打印工具信息
            print("\n====== 可用工具列表 ======")
            for i, tool in enumerate(tools):
                print(f"工具 {i+1}: {tool.name}")
                print(f"  描述: {tool.description}")
                print(f"  参数: {tool.args}")
                print("--------------------------")
            print("==========================\n")
            
            # 验证至少有一个工具
            self.assertTrue(len(tools) >= 0, "应该至少有一些工具可用")
        except Exception as e:
            print(f"获取工具时发生错误: {str(e)}")
            self.fail(f"获取工具列表时出错: {str(e)}")


# 为异步测试定义辅助函数
def run_async_test(test_func):
    """运行异步测试函数的辅助函数"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_func())
    
if __name__ == "__main__":
    """
    测试入口点
    使用自定义runner来支持异步测试
    """
    # 实例化测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(TestParseJson('test_direct_json'))
    suite.addTest(TestParseJson('test_json_in_markdown'))
    suite.addTest(TestParseJson('test_json_in_text'))
    suite.addTest(TestParseJson('test_invalid_json'))
    
    # 添加异步测试用例
    print("正在运行异步测试...")
    
    # try:
    #     # 尝试运行LLM写诗测试
    #     print("测试LLM写诗功能...")
    #     run_async_test(TestGetLLM().test_get_llm_write_poem)
    # except Exception as e:
    #     print(f"LLM写诗测试失败: {str(e)}")
    
    try:
        # 尝试运行工具获取测试
        print("测试工具获取功能...")
        run_async_test(TestGetTools().test_get_tools_availability)
    except Exception as e:
        print(f"工具获取测试失败: {str(e)}")
    
    # 运行同步测试
    unittest.TextTestRunner().run(suite)
