#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务模块 - 统一的任务执行器，支持不同设备参数
"""
import os
import sys
import logging
import random
import string
import shutil
import time
from time import sleep
from typing import List, Dict
from contextlib import contextmanager

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


class TaskRunner:
    """任务执行器 - 根据设备配置执行搜索任务"""
    
    def __init__(self, device_config: Dict, execution_config: Dict, cookie_file: str):
        """
        初始化任务执行器
        
        Args:
            device_config: 设备配置（user_agent等）
            execution_config: 执行配置（搜索次数、延迟等）
            cookie_file: Cookie文件路径
        """
        self.device_config = device_config
        self.execution_config = execution_config
        self.cookie_file = cookie_file
        
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.unique_dir = self._generate_profile_dir()
        self.cookies = self._load_cookies()
        
        # 提取执行配置
        self.max_search_count = execution_config.get('max_search_count', 50)
        self.simulate_typing = execution_config.get('simulate_typing', True)
        self.headless = execution_config.get('headless', False)
        self.base_delay = tuple(execution_config.get('base_delay', [1, 15]))
        self.retry_delay = execution_config.get('retry_delay', 5)
        self.max_retries = execution_config.get('max_retries', 3)
        self.element_timeout = execution_config.get('element_timeout', 5)
        
        logging.info("任务执行器初始化完成 - 设备: %s, 模式: %s", 
                    device_config.get('name', 'Unknown'),
                    "无头" if self.headless else "有头")
    
    def _generate_profile_dir(self) -> str:
        """生成随机浏览器配置目录"""
        return os.path.join(
            self.current_dir,
            "chrome_profile_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        )
    
    @contextmanager
    def _browser_context(self):
        """浏览器上下文管理器"""
        driver = None
        try:
            driver = self._init_browser()
            yield driver
        finally:
            self._safe_quit_browser(driver)
            self._clean_profile_dir()
    
    def _init_browser(self) -> webdriver.Chrome:
        """初始化浏览器实例"""
        options = self._configure_browser_options()
        
        try:
            if uc:
                driver = uc.Chrome(options=options, version_main=None, user_data_dir=self.unique_dir)
            else:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
            
            driver.implicitly_wait(self.element_timeout)
            driver.set_page_load_timeout(30)
            return driver
        except WebDriverException as e:
            logging.error("浏览器初始化失败: %s", str(e))
            raise
    
    def _configure_browser_options(self) -> webdriver.ChromeOptions:
        """配置浏览器选项"""
        if uc:
            options = uc.ChromeOptions()
        else:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.unique_dir}")
        
        # 使用设备配置的 user-agent
        user_agent = self.device_config.get('user_agent', '')
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")
        
        options.add_argument("--log-level=3")

        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

        # 反自动化检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 性能优化参数
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        
        return options
    
    def _load_cookies(self) -> List[Dict]:
        """从文件加载Cookies"""
        if not os.path.exists(self.cookie_file):
            raise FileNotFoundError(f"Cookie文件未找到: {self.cookie_file}")

        cookies = []
        with open(self.cookie_file, "r", encoding="utf-8") as f:
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
                
                if "name" in cookie_dict and "value" in cookie_dict:
                    cookies.append({
                        "name": cookie_dict["name"],
                        "value": cookie_dict["value"],
                        "domain": cookie_dict.get("domain", ".bing.com"),
                        "path": cookie_dict.get("path", "/"),
                        "secure": cookie_dict.get("secure", False)
                    })
                else:
                    for key, value in cookie_dict.items():
                        cookies.append({
                            "name": key,
                            "value": value,
                            "domain": ".bing.com",
                            "path": "/",
                            "secure": False
                        })
        
        if not cookies:
            logging.error("未找到有效Cookie")
        else:
            logging.info("成功加载 %d 个Cookies", len(cookies))
        
        return cookies
    
    def _safe_quit_browser(self, driver: webdriver.Chrome):
        """安全关闭浏览器"""
        try:
            if driver:
                driver.quit()
                logging.info("浏览器实例已安全关闭")
        except Exception as e:
            logging.warning("关闭浏览器时发生错误: %s", str(e))
    
    def _clean_profile_dir(self):
        """清理浏览器配置文件"""
        if os.path.exists(self.unique_dir):
            try:
                shutil.rmtree(self.unique_dir)
                logging.info("已清理浏览器配置文件")
            except Exception as e:
                logging.error("清理配置文件失败: %s", str(e))
    
    def _inject_cookies(self, driver: webdriver.Chrome):
        """注入Cookies到浏览器"""
        driver.get("https://www.bing.com")
        for cookie in self.cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning("注入Cookie失败: %s - %s", cookie.get("name"), str(e))
        logging.info("成功注入 %d 个Cookies", len(self.cookies))
        driver.refresh()
    
    def _handle_consent_dialog(self, driver: webdriver.Chrome):
        """处理隐私协议弹窗"""
        try:
            consent_button = WebDriverWait(driver, self.element_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., '同意') or contains(., '接受')]"))
            )
            consent_button.click()
            sleep(random.uniform(*self.base_delay))
        except TimeoutException:
            pass
    
    def _verify_login_state(self, driver: webdriver.Chrome) -> bool:
        """验证登录状态"""
        try:
            try:
                WebDriverWait(driver, self.element_timeout).until(
                    EC.presence_of_element_located((By.ID, "id_rh"))
                )
                logging.info("用户状态验证成功")
                return True
            except TimeoutException:
                pass
            
            page_source = driver.page_source.lower()
            login_indicators = ["rewards dashboard", "积分", "points", "signed in", "已登录"]
            if any(indicator in page_source for indicator in login_indicators):
                logging.info("用户状态验证成功（页面内容）")
                return True
            
            cookies = driver.get_cookies()
            auth_cookies = [c for c in cookies if any(key in c.get('name', '').lower() for key in ['auth', 'token', 'session'])]
            if auth_cookies:
                logging.info("用户状态验证成功（认证Cookie）")
                return True
            
            logging.warning("无法验证登录状态，但将继续执行")
            return True
        except Exception as e:
            logging.warning("登录状态验证异常: %s", str(e))
            return True
    
    def _perform_search_flow(self, driver: webdriver.Chrome, keyword: str):
        """执行单个搜索流程"""
        try:
            search_box = WebDriverWait(driver, self.element_timeout).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            search_box.clear()
            if self.simulate_typing:
                for char in keyword:
                    search_box.send_keys(char)
                    sleep(random.uniform(0.1, 0.3))
            else:
                search_box.send_keys(keyword)
            
            search_box.send_keys(Keys.RETURN)
            
            WebDriverWait(driver, self.element_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2 > a[href]"))
            )
            logging.debug("搜索结果页加载成功")

        except TimeoutException:
            pass
        except Exception as e:
            logging.warning("执行搜索时出错: %s", str(e))
    
    def _load_search_keywords(self) -> List[str]:
        """加载搜索关键词"""
        keyword_path = os.path.join(self.current_dir, "keyword.txt")
        if not os.path.exists(keyword_path):
            raise FileNotFoundError(f"关键词文件未找到: {keyword_path}")

        with open(keyword_path, "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        if not keywords:
            raise ValueError("关键词文件为空")
        
        logging.info("已加载 %d 个搜索关键词", len(keywords))
        return keywords
    
    def _execute_searches(self, driver: webdriver.Chrome, keywords: List[str]):
        """执行搜索任务"""
        success_count = 0
        retry_counter = 0

        while success_count < self.max_search_count and retry_counter < self.max_retries:
            try:
                keyword = random.choice(keywords)
                logging.info("正在执行搜索 (%d/%d): %s", 
                            success_count+1, self.max_search_count, keyword)
                
                self._perform_search_flow(driver, keyword)
                success_count += 1
                retry_counter = 0
                
                driver.get("https://www.bing.com")
                self._random_delay()

            except Exception as e:
                logging.warning("搜索失败: %s (重试 %d/%d)", 
                               str(e), retry_counter+1, self.max_retries)
                retry_counter += 1
                self._random_delay(base=self.retry_delay)
                
                if retry_counter >= self.max_retries:
                    raise RuntimeError("连续重试超过最大限制")
    
    def _random_delay(self, base: float = None):
        """生成随机延迟"""
        if base is None:
            delay = random.uniform(*self.base_delay)
        else:
            delay = base
        logging.info("等待 %.2f 秒", delay)
        time.sleep(delay)
    
    def run(self) -> Dict:
        """
        执行任务
        
        Returns:
            Dict: 执行结果统计
        """
        start_time = time.time()
        result = {
            "success": False,
            "searches_completed": 0,
            "total_time": 0,
            "error": None
        }
        
        try:
            with self._browser_context() as driver:
                self._inject_cookies(driver)
                self._handle_consent_dialog(driver)
                
                if not self._verify_login_state(driver):
                    raise RuntimeError("登录验证失败，请检查Cookies")

                keywords = self._load_search_keywords()
                self._execute_searches(driver, keywords)
                
                result["success"] = True
                result["searches_completed"] = self.max_search_count
        
        except Exception as e:
            logging.error("任务执行失败: %s", str(e))
            result["error"] = str(e)
        
        finally:
            end_time = time.time()
            result["total_time"] = end_time - start_time
            logging.info("任务执行完成 - 总运行时间: %.2f 秒", result["total_time"])
        
        return result
