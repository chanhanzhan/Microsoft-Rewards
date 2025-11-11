#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Cookie Manager的改进
验证手动登录和智能检测功能
"""
import os
import sys
import json
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_json_cookie_format():
    """测试JSON cookie格式的读写"""
    print("=" * 60)
    print("测试1: JSON Cookie格式")
    print("=" * 60)
    
    # 创建测试cookie
    test_cookies = [
        {
            "name": "test_cookie_1",
            "value": "test_value_1",
            "domain": ".bing.com",
            "path": "/",
            "secure": False
        },
        {
            "name": "test_cookie_2",
            "value": "test_value_2",
            "domain": ".bing.com",
            "path": "/",
            "secure": True
        }
    ]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='_json.txt', delete=False, encoding='utf-8') as f:
        json_file = f.name
        json.dump(test_cookies, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 创建JSON cookie文件: {json_file}")
    
    # 读取并验证
    with open(json_file, 'r', encoding='utf-8') as f:
        loaded_cookies = json.load(f)
    
    if len(loaded_cookies) == 2:
        print(f"✓ 成功加载 {len(loaded_cookies)} 个cookies")
    else:
        print(f"✗ Cookie数量不匹配: 期望2，实际{len(loaded_cookies)}")
        return False
    
    if loaded_cookies[0]['name'] == 'test_cookie_1':
        print(f"✓ Cookie名称正确")
    else:
        print(f"✗ Cookie名称错误")
        return False
    
    # 清理
    os.unlink(json_file)
    print("✓ 测试通过\n")
    return True

def test_text_cookie_format():
    """测试文本cookie格式的读写"""
    print("=" * 60)
    print("测试2: 文本Cookie格式（向后兼容）")
    print("=" * 60)
    
    # 创建测试cookie文本
    test_content = """test_cookie_1=test_value_1; domain=.bing.com; path=/;
test_cookie_2=test_value_2; domain=.bing.com; path=/;
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        text_file = f.name
        f.write(test_content)
    
    print(f"✓ 创建文本cookie文件: {text_file}")
    
    # 读取并解析
    cookies = []
    with open(text_file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            cookie_dict = {}
            for part in line.split(';'):
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    cookie_dict[key.strip()] = value.strip()
            
            if "name" not in cookie_dict and len(cookie_dict) > 0:
                # 第一个键值对是name=value
                first_key = list(cookie_dict.keys())[0]
                cookies.append({
                    "name": first_key,
                    "value": cookie_dict[first_key]
                })
    
    if len(cookies) == 2:
        print(f"✓ 成功解析 {len(cookies)} 个cookies")
    else:
        print(f"✗ Cookie数量不匹配: 期望2，实际{len(cookies)}")
        return False
    
    # 清理
    os.unlink(text_file)
    print("✓ 测试通过\n")
    return True

def test_cookie_manager_import():
    """测试cookie_manager模块导入"""
    print("=" * 60)
    print("测试3: Cookie Manager模块导入")
    print("=" * 60)
    
    try:
        from scripts.cookie_manager import check_login_status_smart, wait_for_manual_login, get_bing_cookies
        print("✓ 成功导入 check_login_status_smart")
        print("✓ 成功导入 wait_for_manual_login")
        print("✓ 成功导入 get_bing_cookies")
        print("✓ 测试通过\n")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Cookie Manager 改进验证测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("JSON Cookie格式", test_json_cookie_format()))
    results.append(("文本Cookie格式", test_text_cookie_format()))
    results.append(("模块导入", test_cookie_manager_import()))
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Cookie Manager改进验证成功。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
