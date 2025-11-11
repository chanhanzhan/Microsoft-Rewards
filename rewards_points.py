#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
积分查询模块 - 获取Microsoft Rewards积分信息
"""
import os
import sys
import logging
from typing import Dict, Optional

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_rewards_points(cookie_file: str) -> Dict:
    """
    获取Microsoft Rewards积分信息
    
    Args:
        cookie_file: Cookie文件路径
        
    Returns:
        Dict: 包含积分信息的字典
    """
    # Validate cookie_file path to prevent path injection
    import re
    cookie_filename = os.path.basename(cookie_file)
    if not re.match(r'^cookie_[a-zA-Z0-9@._-]+\.txt$', cookie_filename):
        return {
            "success": False,
            "available_points": 0,
            "lifetime_points": 0,
            "daily_point_progress": 0,
            "daily_point_max": 0,
            "error": "无效的Cookie文件名"
        }
    
    result = {
        "success": False,
        "available_points": 0,
        "lifetime_points": 0,
        "daily_point_progress": 0,
        "daily_point_max": 0,
        "error": None
    }
    
    try:
        # 配置浏览器
        if uc:
            options = uc.ChromeOptions()
        else:
            options = webdriver.ChromeOptions()
        
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 初始化浏览器
        if uc:
            driver = uc.Chrome(options=options, version_main=None)
        else:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        try:
            # 访问Bing并注入cookies
            driver.get("https://www.bing.com")
            
            # 加载cookies
            if os.path.exists(cookie_file):
                with open(cookie_file, "r", encoding="utf-8") as f:
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
                            try:
                                driver.add_cookie({
                                    "name": cookie_dict["name"],
                                    "value": cookie_dict["value"],
                                    "domain": cookie_dict.get("domain", ".bing.com"),
                                    "path": cookie_dict.get("path", "/"),
                                })
                            except:
                                pass
                
                driver.refresh()
                time.sleep(3)
            
            # 访问Rewards页面
            driver.get("https://rewards.bing.com/")
            time.sleep(5)
            
            # 尝试获取积分信息
            try:
                # 方法1: 从页面元素获取
                points_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-points-breakdown-available-points, .rewardspoints, [data-bi-id='rewards-points']"))
                )
                points_text = points_element.text
                
                # 提取数字
                import re
                numbers = re.findall(r'\d+', points_text.replace(',', ''))
                if numbers:
                    result["available_points"] = int(numbers[0])
                    result["success"] = True
            except TimeoutException:
                # 方法2: 从页面源代码获取
                page_source = driver.page_source
                import re
                
                # 查找积分相关的数据
                points_matches = re.findall(r'"availablePoints["\s:]+(\d+)', page_source)
                if points_matches:
                    result["available_points"] = int(points_matches[0])
                    result["success"] = True
                
                lifetime_matches = re.findall(r'"lifetimePoints["\s:]+(\d+)', page_source)
                if lifetime_matches:
                    result["lifetime_points"] = int(lifetime_matches[0])
                
                # 每日进度
                daily_progress_matches = re.findall(r'"dailySetPromotions.*?"promotionProgress["\s:]+(\d+)', page_source)
                daily_max_matches = re.findall(r'"dailySetPromotions.*?"promotionMax["\s:]+(\d+)', page_source)
                
                if daily_progress_matches and daily_max_matches:
                    result["daily_point_progress"] = int(daily_progress_matches[0])
                    result["daily_point_max"] = int(daily_max_matches[0])
            
            if not result["success"]:
                result["error"] = "无法获取积分信息，可能cookie已失效"
        
        finally:
            driver.quit()
    
    except Exception as e:
        logging.error(f"获取积分失败: {e}")
        result["error"] = str(e)
    
    return result


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 1:
        cookie_file = sys.argv[1]
        points = get_rewards_points(cookie_file)
        print(f"积分信息: {points}")
    else:
        print("用法: python rewards_points.py <cookie_file>")
