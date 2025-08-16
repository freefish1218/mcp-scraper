#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from src.scraper.config import get_server, get_cat_server

async def test_get_server():
    """测试获取服务器信息"""
    print("\n=== 测试 get_server 方法 ===")
    
    try:
        # 测试获取所有服务器
        print("获取所有服务器...")
        servers = await get_server()
        print(f"获取到 {len(servers)} 个服务器")
        
        if not servers:
            print("警告: 没有可用的服务器")
            return
            
        # 打印前几个服务器信息
        print("\n服务器列表:")
        for i, (name, info) in enumerate(list(servers.items())[:3]):  # 最多显示3个
            print(f"{i+1}. {name}: {info}")
        if len(servers) > 3:
            print(f"... 以及另外 {len(servers) - 3} 个服务器")
            
        # 测试获取特定服务器
        server_name = next(iter(servers))
        print(f"\n获取特定服务器 '{server_name}' 的详细信息:")
        server = await get_server(server_name)
        print(server)
        
    except Exception as e:
        print(f"测试 get_server 时发生错误: {str(e)}")
        raise

async def test_get_cat_server():
    """测试按分类获取服务器信息"""
    print("\n=== 测试 get_cat_server 方法 ===")
    
    try:
        # 先获取所有服务器以确定可用的分类
        servers = await get_server()
        if not servers:
            print("警告: 没有可用的服务器")
            return
            
        # 收集所有分类
        categories = set()
        for server in servers.values():
            if server.get("category"):
                categories.update(server["category"])
        
        if not categories:
            print("警告: 没有找到带分类的服务器")
            return
            
        print(f"可用的分类: {sorted(categories)}")
        
        # 测试获取单个分类
        test_category = next(iter(categories))
        print(f"\n获取分类 '{test_category}' 的服务器:")
        cat_servers = await get_cat_server(test_category)
        print(f"找到 {len(cat_servers)} 个服务器:")
        for name, info in cat_servers.items():
            print(f"- {name}: {info}")
            
    except Exception as e:
        print(f"测试 get_cat_server 时发生错误: {str(e)}")
        raise

async def main():
    """主函数"""
    print("=== 开始测试 config 模块 ===\n")
    
    try:
        await test_get_server()
        await test_get_cat_server()
    finally:
        print("\n=== 测试结束 ===")

if __name__ == "__main__":
    asyncio.run(main())
