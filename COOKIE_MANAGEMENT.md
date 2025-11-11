# Cookie 管理改进说明

## 问题背景

原有的 Cookie 管理实现使用自动化填写表单的方式登录 Microsoft 账户，但由于 Microsoft 登录页面的动态特性和防自动化机制，经常出现以下问题：

1. 无法检测到账号输入框
2. 无法检测到密码输入框
3. 登录流程中断或超时

## 解决方案

参考了 [AutoMicrosoftRewards](https://github.com/Meteor-Comet/AutoMicrosoftRewards) 项目的实现，采用**手动登录 + 智能检测**的方式：

### 主要改进

1. **手动登录方式**
   - 启动可视化浏览器（非无头模式）
   - 用户在浏览器中手动完成登录
   - 程序智能检测登录状态
   - 登录成功后自动保存 Cookie

2. **智能登录检测**
   - 多种检测方法组合使用
   - 检查用户头像/用户名元素
   - 检查登录按钮状态变化
   - 检查页面源代码中的登录标识
   - 检查账户相关元素
   - 每5秒自动检查一次，最长等待5分钟

3. **双格式 Cookie 支持**
   - **JSON 格式**（新格式，更可靠）：完整保存所有 Cookie 属性
   - **文本格式**（旧格式，保持兼容）：简化的 Cookie 格式
   - 读取时优先使用 JSON 格式，失败则回退到文本格式

## 使用方法

### 通过 WebUI 刷新 Cookie

1. 访问 WebUI（默认 `http://localhost:5000`）
2. 进入"账户管理"页面
3. 点击需要刷新的账户旁边的"刷新Cookie"按钮
4. 浏览器会自动打开（非无头模式）
5. 在浏览器中手动登录 Microsoft 账户
6. 登录完成后，程序会自动检测并保存 Cookie

### 通过命令行获取 Cookie

```bash
cd scripts
python cookie_manager.py
# 根据提示输入用户名（用于保存 Cookie 文件名）
# 浏览器会自动打开，在浏览器中手动登录
# 登录成功后会自动保存 Cookie
```

## Cookie 文件格式

### JSON 格式（推荐）

文件名：`cookie_<username>_json.txt`

```json
[
  {
    "name": "cookie_name",
    "value": "cookie_value",
    "domain": ".bing.com",
    "path": "/",
    "secure": false,
    "httpOnly": false,
    "expiry": 1234567890
  }
]
```

### 文本格式（兼容）

文件名：`cookie_<username>.txt`

```
cookie_name=cookie_value; domain=.bing.com; path=/;
```

## 技术细节

### 登录检测逻辑

```python
def check_login_status_smart(driver):
    """智能检查登录状态"""
    # 1. 检查URL（避免还在登录页面）
    if "login" in current_url or "oauth" in current_url:
        return False
    
    # 2. 检查用户元素
    user_elements = driver.find_elements(By.CSS_SELECTOR, 
        "[data-testid='user-avatar'], .user-avatar, ...")
    if user_elements:
        return True
    
    # 3. 检查登录按钮文本
    login_element = driver.find_element(By.ID, "id_s")
    if login_text not in ["登录", "Sign in", "Login"]:
        return True
    
    # 4. 检查账户相关元素
    account_elements = driver.find_elements(By.CSS_SELECTOR, 
        "[aria-label*='账户'], [aria-label*='Account'], ...")
    if account_elements:
        return True
    
    # 5. 检查页面内容
    if any(indicator in page_source for indicator in 
           ["rewards", "积分", "points"]):
        return True
    
    return False
```

### Cookie 保存逻辑

```python
# 保存 JSON 格式（新）
json_cookie_file = cookie_file.replace('.txt', '_json.txt')
with open(json_cookie_file, 'w', encoding='utf-8') as f:
    json.dump(cookies, f, ensure_ascii=False, indent=2)

# 保存文本格式（兼容）
with open(cookie_file, "w", encoding="utf-8") as f:
    for c in cookies:
        f.write(f"{c['name']}={c['value']}; domain={c['domain']}; path={c['path']};\n")
```

### Cookie 加载逻辑

```python
# 优先尝试 JSON 格式
json_cookie_path = cookie_path.replace('.txt', '_json.txt')
if os.path.exists(json_cookie_path):
    try:
        with open(json_cookie_path, 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
            # 使用 JSON cookies
            return cookies_list
    except:
        pass

# 回退到文本格式
with open(cookie_path, "r", encoding="utf-8") as f:
    # 解析文本格式 cookies
    ...
```

## 影响的文件

1. `scripts/cookie_manager.py` - Cookie 管理核心模块
2. `scripts/linux.py` - Linux PC 搜索脚本
3. `scripts/win.py` - Windows PC 搜索脚本
4. `scripts/linux-Android.py` - Linux 移动端搜索脚本
5. `scripts/win-Android.py` - Windows 移动端搜索脚本
6. `rewards_points.py` - 积分查询模块
7. `webui.py` - Web 管理界面（使用 cookie_manager）

## 优势

1. **更高的成功率**：避免了自动化填表的检测问题
2. **更好的兼容性**：支持各种登录方式（包括二步验证）
3. **更可靠的存储**：JSON 格式保存完整 Cookie 信息
4. **向后兼容**：仍支持旧的文本格式
5. **用户友好**：可视化浏览器，用户可以看到登录过程

## 注意事项

1. 刷新 Cookie 时会打开可视化浏览器，需要用户手动登录
2. 建议在有图形界面的环境中使用（Windows、macOS、Linux 桌面环境）
3. 首次使用需要手动登录一次，之后 Cookie 可重复使用
4. Cookie 有效期通常为数周到数月，过期后需要重新登录

## 测试

运行测试脚本验证改进：

```bash
python test_cookie_manager.py
```

测试内容包括：
- JSON Cookie 格式读写
- 文本 Cookie 格式读写（向后兼容）
- 模块导入验证
