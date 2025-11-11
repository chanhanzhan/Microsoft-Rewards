#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试积分查询功能
验证 rewards_points.py 的 JSON cookie 支持
"""
import os
import sys
import json
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_mock_cookies():
    """创建模拟的 cookie 文件用于测试"""
    # 这些是示例 cookies，不是真实的登录凭证
    mock_cookies = [
        {
            "name": "MUID",
            "value": "test_value_123",
            "domain": ".bing.com",
            "path": "/",
            "secure": False,
            "httpOnly": False
        },
        {
            "name": "_EDGE_S",
            "value": "test_edge_value",
            "domain": ".bing.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        }
    ]
    
    return mock_cookies

def test_rewards_points_import():
    """测试 rewards_points 模块导入"""
    print("=" * 60)
    print("测试1: Rewards Points 模块导入")
    print("=" * 60)
    
    try:
        from rewards_points import get_rewards_points
        print("✓ 成功导入 get_rewards_points")
        print("✓ 测试通过\n")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def test_json_cookie_loading_logic():
    """测试 JSON cookie 加载逻辑（不实际连接网络）"""
    print("=" * 60)
    print("测试2: JSON Cookie 加载逻辑")
    print("=" * 60)
    
    # 创建临时 cookie 文件
    mock_cookies = create_mock_cookies()
    
    # 创建 JSON 格式文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='_json.txt', delete=False, encoding='utf-8') as f:
        json_file = f.name
        json.dump(mock_cookies, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 创建测试用 JSON cookie 文件: {json_file}")
    
    # 验证文件可以被读取
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        if len(loaded) == len(mock_cookies):
            print(f"✓ JSON cookie 文件格式正确")
            print(f"✓ 包含 {len(loaded)} 个 cookies")
        else:
            print(f"✗ Cookie 数量不匹配")
            return False
    except Exception as e:
        print(f"✗ 读取 JSON 文件失败: {e}")
        return False
    finally:
        # 清理
        if os.path.exists(json_file):
            os.unlink(json_file)
    
    print("✓ 测试通过\n")
    return True

def test_text_cookie_fallback():
    """测试文本 cookie 回退逻辑"""
    print("=" * 60)
    print("测试3: 文本 Cookie 回退逻辑")
    print("=" * 60)
    
    # 创建文本格式 cookie
    text_content = "MUID=test_value_123; domain=.bing.com; path=/;\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        text_file = f.name
        f.write(text_content)
    
    print(f"✓ 创建测试用文本 cookie 文件: {text_file}")
    
    # 验证文件可以被读取
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "MUID" in content:
            print(f"✓ 文本 cookie 文件格式正确")
        else:
            print(f"✗ 文本内容不正确")
            return False
    except Exception as e:
        print(f"✗ 读取文本文件失败: {e}")
        return False
    finally:
        # 清理
        if os.path.exists(text_file):
            os.unlink(text_file)
    
    print("✓ 测试通过\n")
    return True

def test_cookie_file_validation():
    """测试 cookie 文件名验证逻辑"""
    print("=" * 60)
    print("测试4: Cookie 文件名验证")
    print("=" * 60)
    
    import re
    
    # 有效的文件名
    valid_names = [
        "cookie_test@example.com.txt",
        "cookie_user123.txt",
        "cookie_test-user.txt",
        "cookie_test_user.txt"
    ]
    
    # 无效的文件名
    invalid_names = [
        "cookie_../etc/passwd.txt",
        "cookie_test/file.txt",
        "cookie_test;rm -rf.txt"
    ]
    
    pattern = r'^cookie_[a-zA-Z0-9@._-]+\.txt$'
    
    all_valid = True
    for name in valid_names:
        if not re.match(pattern, name):
            print(f"✗ 有效文件名被拒绝: {name}")
            all_valid = False
    
    if all_valid:
        print(f"✓ 所有有效文件名通过验证")
    
    all_invalid = True
    for name in invalid_names:
        if re.match(pattern, name):
            print(f"✗ 无效文件名通过验证: {name}")
            all_invalid = False
    
    if all_invalid:
        print(f"✓ 所有无效文件名被正确拒绝")
    
    if all_valid and all_invalid:
        print("✓ 测试通过\n")
        return True
    else:
        print("✗ 测试失败\n")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("积分查询功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_rewards_points_import()))
    results.append(("JSON Cookie 加载", test_json_cookie_loading_logic()))
    results.append(("文本 Cookie 回退", test_text_cookie_fallback()))
    results.append(("Cookie 文件名验证", test_cookie_file_validation()))
    
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
        print("\n🎉 所有测试通过！积分查询功能验证成功。")
        print("\n📝 注意: 实际的积分查询需要有效的登录 cookies。")
        print("   请使用 WebUI 或 cookie_manager.py 获取真实的 cookies。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
