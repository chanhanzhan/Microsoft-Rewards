#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化调度器 - 实现24小时内随机运行的定时任务
"""
import os
import sys
import time
import random
import logging
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager
from task_runner import TaskRunner
from scripts.cookie_manager import is_cookie_valid, get_bing_cookies

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AutomationScheduler:
    """自动化调度器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.running = False
        self.stop_event = Event()
        self.thread = None
        self.next_run_time = None
        self.last_run_date = None
    
    def start(self):
        """启动调度器"""
        if self.running:
            logging.warning("调度器已在运行")
            return
        
        self.running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        logging.info("调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("调度器已停止")
    
    def is_running(self) -> bool:
        """检查调度器是否运行"""
        return self.running
    
    def get_next_run_time(self) -> Optional[str]:
        """获取下次运行时间"""
        if self.next_run_time:
            return self.next_run_time.isoformat()
        return None
    
    def _run_loop(self):
        """调度循环"""
        automation_config = self.config_manager.get('automation')
        mode = automation_config.get('mode', 'random_24h')
        first_run_on_start = automation_config.get('first_run_on_start', True)
        
        # 首次启动立即运行
        if first_run_on_start:
            logging.info("首次启动，立即执行任务")
            self._execute_all_tasks()
            self.last_run_date = datetime.now().date()
        
        while self.running and not self.stop_event.is_set():
            try:
                # 计算下次运行时间
                if mode == 'random_24h':
                    self.next_run_time = self._calculate_next_random_time()
                else:
                    # 其他模式可以在这里扩展
                    self.next_run_time = self._calculate_next_random_time()
                
                logging.info(f"下次运行时间: {self.next_run_time}")
                
                # 等待到下次运行时间
                while self.running and not self.stop_event.is_set():
                    now = datetime.now()
                    if now >= self.next_run_time:
                        break
                    
                    # 每分钟检查一次
                    wait_time = min(60, (self.next_run_time - now).total_seconds())
                    if wait_time > 0:
                        self.stop_event.wait(timeout=wait_time)
                
                if not self.running:
                    break
                
                # 执行任务
                current_date = datetime.now().date()
                if self.last_run_date != current_date:
                    logging.info("开始执行定时任务")
                    self._execute_all_tasks()
                    self.last_run_date = current_date
                else:
                    logging.info("今日已执行任务，跳过")
            
            except Exception as e:
                logging.error(f"调度循环出错: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def _calculate_next_random_time(self) -> datetime:
        """计算下次随机运行时间（在接下来24小时内）"""
        now = datetime.now()
        
        # 检查今天是否已运行
        if self.last_run_date == now.date():
            # 今天已运行，计算明天的随机时间
            tomorrow = now + timedelta(days=1)
            start_of_tomorrow = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            random_seconds = random.randint(0, 24 * 60 * 60)
            return start_of_tomorrow + timedelta(seconds=random_seconds)
        else:
            # 今天还没运行，在今天剩余时间内随机选择
            remaining_seconds = (24 - now.hour) * 3600 - now.minute * 60 - now.second
            if remaining_seconds > 3600:  # 至少保留1小时
                random_seconds = random.randint(60, remaining_seconds)
                return now + timedelta(seconds=random_seconds)
            else:
                # 剩余时间不足，选择明天的随机时间
                tomorrow = now + timedelta(days=1)
                start_of_tomorrow = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
                random_seconds = random.randint(0, 24 * 60 * 60)
                return start_of_tomorrow + timedelta(seconds=random_seconds)
    
    def _execute_all_tasks(self):
        """执行所有账户的任务"""
        accounts = self.config_manager.get_accounts()
        
        if not accounts:
            logging.warning("没有配置账户")
            return
        
        for account in accounts:
            username = account.get('username')
            logging.info(f"执行账户 {username} 的任务")
            
            try:
                self._execute_account_task(username)
            except Exception as e:
                logging.error(f"账户 {username} 任务执行失败: {e}", exc_info=True)
    
    def _execute_account_task(self, username: str):
        """执行单个账户的任务"""
        account = None
        for acc in self.config_manager.get_accounts():
            if acc.get('username') == username:
                account = acc
                break
        
        if not account:
            logging.error(f"账户 {username} 不存在")
            return
        
        # 检查并获取cookie
        cookie_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"cookie_{username}.txt"
        )
        
        if not is_cookie_valid(username=username, cookie_file=cookie_file):
            logging.info(f"账户 {username} 的cookie无效或不存在，需要初始化登录")
            password = account.get('password')
            if not password:
                logging.error(f"账户 {username} 没有配置密码，跳过")
                return
            
            try:
                get_bing_cookies(username, password, headless=False, cookie_file=cookie_file)
            except Exception as e:
                logging.error(f"账户 {username} 登录失败: {e}")
                return
        
        # 执行PC设备任务
        devices_config = self.config_manager.get('devices')
        execution_config = self.config_manager.get('execution')
        
        if devices_config.get('pc', {}).get('enabled', True):
            logging.info(f"账户 {username} - 执行PC任务")
            pc_device_config = {
                'name': 'PC',
                'user_agent': devices_config['pc']['user_agent']
            }
            try:
                runner = TaskRunner(pc_device_config, execution_config, cookie_file)
                result = runner.run()
                logging.info(f"PC任务完成: {result}")
            except Exception as e:
                logging.error(f"PC任务失败: {e}", exc_info=True)
        
        # 执行Mobile设备任务
        if devices_config.get('mobile', {}).get('enabled', True):
            logging.info(f"账户 {username} - 执行Mobile任务")
            mobile_device_config = {
                'name': 'Mobile',
                'user_agent': devices_config['mobile']['user_agent']
            }
            try:
                runner = TaskRunner(mobile_device_config, execution_config, cookie_file)
                result = runner.run()
                logging.info(f"Mobile任务完成: {result}")
            except Exception as e:
                logging.error(f"Mobile任务失败: {e}", exc_info=True)
    
    def run_manual_task(self, username: Optional[str] = None, device: str = 'all'):
        """
        手动运行任务
        
        Args:
            username: 用户名，None表示所有用户
            device: 设备类型 (pc, mobile, all)
        """
        accounts = self.config_manager.get_accounts()
        
        if username:
            accounts = [acc for acc in accounts if acc.get('username') == username]
        
        if not accounts:
            logging.warning("没有找到匹配的账户")
            return {"success": False, "error": "没有找到匹配的账户"}
        
        results = []
        for account in accounts:
            uname = account.get('username')
            logging.info(f"手动执行账户 {uname} 的任务 (设备: {device})")
            
            try:
                result = self._execute_manual_account_task(uname, device)
                results.append(result)
            except Exception as e:
                logging.error(f"账户 {uname} 任务执行失败: {e}", exc_info=True)
                results.append({"username": uname, "success": False, "error": str(e)})
        
        return {"success": True, "results": results}
    
    def _execute_manual_account_task(self, username: str, device: str):
        """手动执行单个账户的任务"""
        account = None
        for acc in self.config_manager.get_accounts():
            if acc.get('username') == username:
                account = acc
                break
        
        if not account:
            return {"username": username, "success": False, "error": "账户不存在"}
        
        cookie_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"cookie_{username}.txt"
        )
        
        if not is_cookie_valid(username=username, cookie_file=cookie_file):
            password = account.get('password')
            if not password:
                return {"username": username, "success": False, "error": "没有配置密码"}
            
            try:
                get_bing_cookies(username, password, headless=False, cookie_file=cookie_file)
            except Exception as e:
                return {"username": username, "success": False, "error": f"登录失败: {e}"}
        
        devices_config = self.config_manager.get('devices')
        execution_config = self.config_manager.get('execution')
        results = []
        
        if device in ['pc', 'all'] and devices_config.get('pc', {}).get('enabled', True):
            pc_device_config = {
                'name': 'PC',
                'user_agent': devices_config['pc']['user_agent']
            }
            try:
                runner = TaskRunner(pc_device_config, execution_config, cookie_file)
                result = runner.run()
                results.append({"device": "pc", "result": result})
            except Exception as e:
                results.append({"device": "pc", "success": False, "error": str(e)})
        
        if device in ['mobile', 'all'] and devices_config.get('mobile', {}).get('enabled', True):
            mobile_device_config = {
                'name': 'Mobile',
                'user_agent': devices_config['mobile']['user_agent']
            }
            try:
                runner = TaskRunner(mobile_device_config, execution_config, cookie_file)
                result = runner.run()
                results.append({"device": "mobile", "result": result})
            except Exception as e:
                results.append({"device": "mobile", "success": False, "error": str(e)})
        
        return {"username": username, "success": True, "devices": results}


if __name__ == '__main__':
    # 测试调度器
    config_manager = ConfigManager()
    scheduler = AutomationScheduler(config_manager)
    
    print("启动调度器...")
    scheduler.start()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n停止调度器...")
        scheduler.stop()
