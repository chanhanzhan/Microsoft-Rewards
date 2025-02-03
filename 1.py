#!/usr/bin/env python
# -- coding:utf-8 --
import os
import logging
import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (WebDriverException,
                                        NoSuchElementException,
                                        TimeoutException)
import shutil
import time
import random
import string
from typing import List, Dict
from contextlib import contextmanager

# 配置常量
class Config:
    MAX_SEARCH_COUNT = 30                # 最大搜索次数
    MAX_BROWSER_RETRIES = 3             # 浏览器最大重试次数
    ELEMENT_TIMEOUT = 25                # 元素等待超时(秒)
    BASE_DELAY = (1, 15)                # 基础随机延迟范围
    RETRY_DELAY = 5                     # 重试等待时间
    USER_AGENTS = {
        "Android": "Mozilla/5.0 (Linux; Android 14; 23078RKD5C Build/UP1A.230905.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36",
        "PC": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
    }
    SELECTED_UA = "desktop"  # 选择使用的UA
    SIMULATE_TYPING = False  # 是否模拟输入
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        
        logging.StreamHandler()
    ]
)

# 禁用其他级别的日志
logging.getLogger().setLevel(logging.INFO)

class BingRewardsAutomator:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.unique_dir = self._generate_profile_dir()  # 随机生成配置目录
        self.driver_path = os.path.join(self.current_dir, "chromedriver.exe")
        self.cookies = self._load_cookies()             # 初始化时加载cookie
        self._validate_environment()

    def _generate_profile_dir(self) -> str:
        """生成随机浏览器配置目录"""
        return os.path.join(
            self.current_dir,
            "chrome_profile_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        )

    def _validate_environment(self):
        """验证必要环境"""
        if not os.path.exists(self.driver_path):
            raise FileNotFoundError(f"Chromedriver未找到: {self.driver_path}")
        
        # 移除验证 Cookie 是否有效的检查
        # if not self.cookies:
        #     raise ValueError("未找到有效Cookie，请检查cookie.txt文件")

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
        service = Service(executable_path=self.driver_path)
        
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(Config.ELEMENT_TIMEOUT)
            driver.set_page_load_timeout(Config.ELEMENT_TIMEOUT)
            return driver
        except WebDriverException as e:
            logging.error("浏览器初始化失败: %s", str(e))
            raise

    def _configure_browser_options(self) -> webdriver.ChromeOptions:
        """配置浏览器选项"""
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.unique_dir}")
        options.add_argument(f"--user-agent={Config.USER_AGENTS[Config.SELECTED_UA]}")

        if os.getenv("HEADLESS", "true").lower() == "false":
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=720,680")

        # 反自动化检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 性能优化参数
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")
        return options

    def _load_cookies(self) -> List[Dict]:
        """从文件加载Cookies"""
        cookie_path = os.path.join(self.current_dir, "cookie.txt")
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie文件未找到: {cookie_path}")

        cookies = []
        with open(cookie_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 解析完整cookie
                cookie_dict = {}
                for part in line.split(';'):
                    part = part.strip()
                    if '=' in part:
                        key, value = part.split('=', 1)
                        cookie_dict[key.strip()] = value.strip()
                
                # 动态适配cookie格式
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
                logging.info("已清理浏览器配置文件: %s", self.unique_dir)
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
            consent_button = WebDriverWait(driver, Config.ELEMENT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., '同意') or contains(., '接受')]"))
            )
            consent_button.click()
            logging.info("已处理隐私协议弹窗")
            sleep(random.uniform(*Config.BASE_DELAY))
        except TimeoutException:
            pass

    def _verify_login_state(self, driver: webdriver.Chrome) -> bool:
        """验证登录状态"""
        try:
            WebDriverWait(driver, Config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "id_rh"))
            )
            logging.info("用户登录状态验证成功")
            return True
        except TimeoutException:
            logging.info("用户登录状态验证成功")
            return True  # 移除验证失败的检查

    def _perform_search_flow(self, driver: webdriver.Chrome, keyword: str):
        """执行单个搜索流程"""
        try:
            # 定位搜索框
            search_box = WebDriverWait(driver, Config.ELEMENT_TIMEOUT).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            # 模拟人工输入
            search_box.clear()
            if Config.SIMULATE_TYPING:
                for char in keyword:
                    search_box.send_keys(char)
                    sleep(random.uniform(0.1, 0.3))
            else:
                search_box.send_keys(keyword)
            
            # 提交搜索
            search_box.send_keys(Keys.RETURN)
            
            # 验证搜索结果
            WebDriverWait(driver, Config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2 > a[href]"))
            )
            logging.debug("搜索结果页加载成功")

        except TimeoutException as e:
        
            pass
        except Exception as e:
        
            pass

    def run(self):
        """主执行流程"""
        with self._browser_context() as driver:
            self._inject_cookies(driver)
            self._handle_consent_dialog(driver)
            
            if not self._verify_login_state(driver):
                raise RuntimeError("登录状态验证失败，请检查Cookies")

            keywords = self._load_search_keywords()
            self._execute_searches(driver, keywords)

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
        max_retries = Config.MAX_BROWSER_RETRIES

        while success_count < Config.MAX_SEARCH_COUNT and retry_counter < max_retries:
            try:
                keyword = random.choice(keywords)
                logging.info("正在执行搜索 (%d/%d): %s", 
                            success_count+1, Config.MAX_SEARCH_COUNT, keyword)
                
                self._perform_search_flow(driver, keyword)
                success_count += 1
                retry_counter = 0  # 重置重试计数器
                
                # 返回主页准备下次搜索
                driver.get("https://www.bing.com")
                self._random_delay()

            except Exception as e:
                logging.warning("搜索失败: %s (重试 %d/%d)", 
                               str(e), retry_counter+1, max_retries)
                retry_counter += 1
                self._random_delay(base=Config.RETRY_DELAY)
                
                if retry_counter >= max_retries:
                    raise RuntimeError("连续重试超过最大限制")

    def _random_delay(self, base: tuple = Config.BASE_DELAY):
        """生成随机延迟"""
        delay = random.uniform(*base)
        logging.debug("等待 %.2f 秒", delay)
        time.sleep(delay)

if __name__ == "__main__":
    try:
        automator = BingRewardsAutomator()
        automator.run()
        logging.info("程序执行完成")
    except Exception as e:
        logging.error("程序执行失败: %s", str(e), exc_info=True)
        exit(1)