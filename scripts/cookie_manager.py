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

def get_bing_cookies(username, password, driver_path=None, headless=True, cookie_file=None):
    """
    获取Bing Cookie，不再需要手动指定driver_path
    如果安装了undetected_chromedriver，会优先使用它来避免检测
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; 23078RKD5C Build/UP1A.230905.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36"
    ]
    
    # 使用undetected_chromedriver（如果可用）或标准selenium
    if uc:
        options = uc.ChromeOptions()
        options.add_argument("--incognito")
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
        options.add_argument("--incognito")
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
    
    driver.get("https://login.live.com/")
    try:
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                # 等待15秒加载页面
                time.sleep(15)
                # 判断账号输入框是否存在
                email_input = driver.find_element(By.NAME, "loginfmt")
                if email_input:
                    break
            except Exception:
                retry_count += 1
                print(f"未检测到账号输入框，刷新页面重试（第{retry_count}次）...")
                driver.refresh()
        else:
            print("多次尝试后仍未检测到账号输入框，登录失败！")
            driver.quit()
            return
        # 输入账号
        email_input.send_keys(username)
        email_input.send_keys(Keys.RETURN)
        # 等待密码输入框出现
        time.sleep(15)
        retry_count = 0
        while retry_count < max_retries:
            try:
                pwd_input = driver.find_element(By.NAME, "passwd")
                if pwd_input:
                    break
            except Exception:
                retry_count += 1
                print(f"未检测到密码输入框，刷新页面重试（第{retry_count}次）...")
                driver.refresh()
                time.sleep(15)
        else:
            print("多次尝试后仍未检测到密码输入框，登录失败！")
            driver.quit()
            return
        pwd_input.send_keys(password)
        pwd_input.send_keys(Keys.RETURN)
        clicked = False
        for _ in range(3):
            try:
                btn = None
               
                try:
                    btn = driver.execute_script("return document.querySelector('#acceptButton')")
                except Exception:
                    pass
                # 2. Selenium By.ID
                if not btn:
                    try:
                        btn = driver.find_element(By.ID, "acceptButton")
                    except Exception:
                        pass
                # 3. XPath文本
                if not btn:
                    try:
                        btn = driver.find_element(By.XPATH, "//button[text()='是']")
                    except Exception:
                        pass
                # 4. aria-label
                if not btn:
                    try:
                        btn = driver.find_element(By.XPATH, "//button[@aria-label='是']")
                    except Exception:
                        pass
                # 5. 其它降级方式（老按钮）
                if not btn:
                    try:
                        btn = driver.find_element(By.ID, "idSIButton9")
                    except Exception:
                        pass
                if btn:
                    # 高亮显示目标按钮
                    driver.execute_script("arguments[0].style.border='3px solid red';", btn)
                    # 直接用 JS click
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                        break
                    except Exception:
                        pass
                    # ActionChains offset点击
                    try:
                        actionchains_offset_click(driver, btn, 0.5, 0.5)
                        clicked = True
                        break
                    except Exception:
                        pass
                    # CDP点击
                    try:
                        cdp_click(driver, btn, 0.5, 0.5)
                        clicked = True
                        break
                    except Exception:
                        pass
                time.sleep(2)
            except Exception:
                time.sleep(2)
        if not clicked:
            print("未能自动点击'保持登录状态'按钮，请手动点击！")
            try:
                driver.find_element(By.TAG_NAME, "body").click()
            except Exception:
                pass
            time.sleep(15)
        # 等待登录完成并验证
        time.sleep(5)
      
        # 访问账户页面验证登录状态
        driver.get("https://account.microsoft.com/")
        time.sleep(5)
       
        # 更健壮的登录验证
        page_source = driver.page_source.lower()
        is_logged_in = any(keyword in page_source for keyword in ["账户", "account", "profile", "个人资料"])
        
        if not is_logged_in:
            print("登录后未检测到账户主页，cookie 可能无效！")
        else:
            print("登录验证成功！")
        
        cookies = driver.get_cookies()
        driver.quit()
        if not cookie_file:
            cookie_file = os.path.join(os.path.dirname(__file__), "..", f"cookie_{username}.txt")
        with open(cookie_file, "w", encoding="utf-8") as f:
            for c in cookies:
                f.write(f"{c['name']}={c['value']}; domain={c['domain']}; path={c['path']};\n")
        print(f"cookie 已保存到 {cookie_file}")
    except Exception as e:
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