#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 normalize_url 函数对图片 URL 的处理
"""
from scraper.utils.url import normalize_url

# 测试用例
test_cases = [
    # 普通 URL
    ("https://example.com?utm_source=google", "https://example.com"),
    # 带有多个参数的 URL
    ("https://example.com?param1=value1&utm_source=google", "https://example.com?param1=value1"),
    # 图片 URL 带参数
    ("https://sergii.tatarenkov.name/images/keyclu/screenshot_2.png?2", "https://sergii.tatarenkov.name/images/keyclu/screenshot_2.png"),
    # 图片 URL 带多个参数
    ("https://example.com/image.jpg?width=100&height=200", "https://example.com/image.jpg"),
    # 图片 URL 带跟踪参数
    ("https://example.com/photo.png?utm_source=google", "https://example.com/photo.png"),
    # 不同格式的图片 URL
    ("https://example.com/image.webp?v=2", "https://example.com/image.webp"),
    # 大写扩展名的图片 URL
    ("https://example.com/IMAGE.JPG?cache=123", "https://example.com/IMAGE.JPG"),
]

# 运行测试
for i, (input_url, expected_output) in enumerate(test_cases):
    result = normalize_url(input_url)
    status = "✅ 通过" if result == expected_output else f"❌ 失败 (得到: {result}, 期望: {expected_output})"
    print(f"测试 {i+1}: {status}")
    print(f"  输入: {input_url}")
    print(f"  输出: {result}")
    print()
