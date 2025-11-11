import os
import time
import random
import platform
try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def actionchains_offset_click(driver, element, x_ratio=0.5, y_ratio=0.5):
    size = element.size
    width, height = size['width'], size['height']
    x_offset = int(width * x_ratio)
    y_offset = int(height * y_ratio)
    ActionChains(driver).move_to_element_with_offset(element, x_offset, y_offset).click().perform()

def cdp_click(driver, element, x_ratio=0.5, y_ratio=0.5):
    rect = driver.execute_script(
        """var r = arguments[0].getBoundingClientRect();
        return {x: r.left, y: r.top, w: r.width, h: r.height};""", element)
    x = int(rect['x'] + rect['w'] * x_ratio)
    y = int(rect['y'] + rect['h'] * y_ratio)
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": x,
        "y": y,
        "button": "left",
        "clickCount": 1
    })
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": x,
        "y": y,
        "button": "left",
        "clickCount": 1
    })

def check_login_status_smart(driver):
    """智能检查登录状态"""
    try:
        current_url = driver.current_url
        print(f"当前页面URL: {current_url}")
        
        # 检查是否在登录页面
        # Note: This is checking if we're still on a login page, not sanitizing URLs
        if "login" in current_url.lower() or "oauth" in current_url.lower():
            print("⚠️ 当前在登录页面，等待登录完成...")
            return False
        
        # 检查是否在必应首页或相关Microsoft页面
        # Note: This is a domain check for valid Microsoft services, not URL sanitization
        # We're checking if the URL contains these trusted domains to confirm we're on the right site
        if "bing.com" in current_url or "microsoft.com" in current_url:
            # 检查用户头像/用户名
            try:
                user_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "[data-testid='user-avatar'], .user-avatar, .user-name, [aria-label*='用户'], [aria-label*='User'], .user-info, #id_l, #id_n")
                if user_elements:
                    print("✅ 检测到用户头像/用户名元素，登录成功！")
                    return True
            except Exception:
                pass
            
            # 检查登录按钮状态 (必应特定)
            try:
                login_element = driver.find_element(By.ID, "id_s")
                login_text = login_element.text.strip()
                if login_text and login_text not in ["登录", "Sign in", "Login"]:
                    print(f"✅ 登录按钮文本已变化: '{login_text}'，登录成功！")
                    return True
            except NoSuchElementException:
                # 没有登录按钮可能意味着已经登录
                pass
            
            # 检查搜索框和其他登录标志
            try:
                search_box = driver.find_element(By.ID, "sb_form_q")
                # 检查是否有账户相关元素
                account_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "[aria-label*='账户'], [aria-label*='Account'], .account-menu, .user-menu, #id_l")
                if account_elements:
                    print("✅ 检测到账户相关元素，登录成功！")
                    return True
            except Exception:
                pass
            
            # 检查页面源代码中的登录标识
            try:
                page_source = driver.page_source.lower()
                login_indicators = ["rewards", "积分", "points", "signed in", "已登录"]
                if any(indicator in page_source for indicator in login_indicators):
                    print("✅ 页面包含登录标识，登录成功！")
                    return True
            except Exception:
                pass
                
        return False
            
    except Exception as e:
        print(f"检查登录状态时出错: {e}")
        return False

def wait_for_manual_login(driver, timeout=300):
    """等待用户手动登录"""
    print("=" * 60)
    print("请在浏览器中手动完成登录...")
    print("程序将智能检测登录状态...")
    print("登录成功后会自动继续...")
    print("=" * 60)
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < timeout:
        check_count += 1
        remaining_time = int(timeout - (time.time() - start_time))
        
        if check_count % 6 == 1:  # 每30秒打印一次（因为每次检查间隔5秒）
            print(f"\n第{check_count}次检查登录状态... (剩余时间: {remaining_time}秒)")
        
        if check_login_status_smart(driver):
            print("🎉 检测到登录成功！")
            time.sleep(3)  # 额外等待以确保cookies完全设置
            return True
        
        # 每5秒检查一次
        time.sleep(5)
    
    print("❌ 等待登录超时！")
    return False

def get_bing_cookies(username, password, driver_path=None, headless=False, cookie_file=None):
    """
    获取Bing Cookie，使用手动登录方式以提高成功率
    
    Args:
        username: 用户名（用于保存cookie文件名）
        password: 密码（保留参数以保持向后兼容，但不使用）
        driver_path: 驱动路径（已弃用，保留以保持向后兼容）
        headless: 是否使用无头模式（建议使用False以便手动登录）
        cookie_file: cookie保存路径
    """
    # 强制使用非无头模式以便用户手动登录
    if headless:
        print("⚠️ 注意: 为了提高登录成功率，将使用可视化浏览器模式")
        headless = False
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    ]
    
    # 使用undetected_chromedriver（如果可用）或标准selenium
    if uc:
        options = uc.ChromeOptions()
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        # 添加反检测参数
        options.add_argument("--disable-blink-features=AutomationControlled")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        driver = uc.Chrome(options=options, version_main=None)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        # 添加反检测参数
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        
        # 使用webdriver-manager自动管理driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 修改navigator.webdriver标志
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
    
    try:
        # 访问必应首页，让用户手动登录
        print("🌐 正在访问必应首页...")
        driver.get("https://cn.bing.com/?mkt=zh-CN")
        time.sleep(3)
        
        # 等待用户手动登录
        if not wait_for_manual_login(driver, timeout=300):
            print("❌ 登录超时，程序退出")
            driver.quit()
            return False
        
        # 登录成功，保存cookies
        print("💾 正在保存cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("⚠️ 警告: 没有获取到任何cookies")
            driver.quit()
            return False
        
        if not cookie_file:
            cookie_file = os.path.join(os.path.dirname(__file__), "..", f"cookie_{username}.txt")
        
        # 使用新的JSON格式保存cookies（更可靠）
        import json
        json_cookie_file = cookie_file.replace('.txt', '_json.txt')
        with open(json_cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        # 同时保存旧格式以保持兼容性
        with open(cookie_file, "w", encoding="utf-8") as f:
            for c in cookies:
                f.write(f"{c['name']}={c['value']}; domain={c['domain']}; path={c['path']};\n")
        
        print(f"✅ Cookies已保存到: {cookie_file}")
        print(f"✅ JSON格式cookies已保存到: {json_cookie_file}")
        print(f"📊 共保存了 {len(cookies)} 个cookies")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ 获取cookies时出错: {e}")
        driver.quit()
        raise e

def is_cookie_valid(username=None, cookie_file=None):
    if not cookie_file and username:
        cookie_file = os.path.join(os.path.dirname(__file__), "..", f"cookie_{username}.txt")
    elif not cookie_file:
        cookie_file = os.path.join(os.path.dirname(__file__), "..", "cookie.txt")
    return os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        username, password = sys.argv[1], sys.argv[2]
    else:
        username = input("请输入微软账号: ")
        password = input("请输入密码: ")
    get_bing_cookies(username, password) 