#!/usr/bin/env python3
import sys
import os
import importlib.util
import traceback

sys.path.insert(0, os.getcwd())

# List of test files to run
test_files = [
    'tests/test_config.py',
    'tests/test_env_detection.py', 
    'tests/test_integration.py',
    'tests/test_llm_util.py',
    'tests/test_normalize_url.py',
    'tests/test_print_article_info.py',
    'tests/test_scraper_url.py',
    'tests/test_scraper_urls.py',
    'tests/test_stealth.py'
]

print("🧪 运行所有测试文件...")
print("=" * 60)

passed = 0
failed = 0

for test_file in test_files:
    print(f"\n📋 运行 {test_file}...")
    
    if not os.path.exists(test_file):
        print(f"❌ 文件不存在: {test_file}")
        failed += 1
        continue
    
    try:
        # Load and execute the test module
        spec = importlib.util.spec_from_file_location("test_module", test_file)
        test_module = importlib.util.module_from_spec(spec)
        
        # Execute the module
        spec.loader.exec_module(test_module)
        
        # If the module has a main function, call it
        if hasattr(test_module, 'main'):
            result = test_module.main()
            # If main function returns None or True, consider it passed
            if result is None or result:
                print(f"✅ {test_file} 通过")
                passed += 1
            else:
                print(f"❌ {test_file} 失败")
                failed += 1
        else:
            print(f"✅ {test_file} 执行完成 (无main函数)")
            passed += 1
            
    except Exception as e:
        print(f"❌ {test_file} 执行出错: {e}")
        traceback.print_exc()
        failed += 1

print("\n" + "=" * 60)
print(f"📊 测试结果总结:")
print(f"   ✅ 通过: {passed}")
print(f"   ❌ 失败: {failed}")
print(f"   📈 总计: {passed + failed}")

if failed == 0:
    print("\n🎉 所有测试都通过了！")
else:
    print(f"\n⚠️  有 {failed} 个测试失败")

sys.exit(0 if failed == 0 else 1)