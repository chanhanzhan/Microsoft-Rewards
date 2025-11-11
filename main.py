#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主入口 - 支持命令行模式和WebUI模式
"""
import sys
import os
import argparse
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def run_cli_mode(config_manager: ConfigManager, username: str = None, device: str = 'all'):
    """命令行模式 - 执行任务"""
    # Import dependencies only when needed
    from task_runner import TaskRunner
    from scripts.cookie_manager import is_cookie_valid, get_bing_cookies
    
    # 首先运行 api.py 获取关键词
    try:
        import subprocess
        subprocess.run([sys.executable, "api.py"], check=True)
    except Exception as e:
        logging.warning(f"获取关键词失败: {e}")
    
    accounts = config_manager.get_accounts()
    
    if not accounts:
        logging.error("没有配置账户，请先添加账户")
        return
    
    # 如果指定用户名，只执行该用户
    if username:
        accounts = [acc for acc in accounts if acc.get('username') == username]
        if not accounts:
            logging.error(f"账户 {username} 不存在")
            return
    
    for account in accounts:
        uname = account['username']
        password = account.get('password')
        
        logging.info(f"处理账户: {uname}")
        
        # 检查和获取cookie
        cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{uname}.txt")
        
        if not is_cookie_valid(username=uname, cookie_file=cookie_file):
            logging.info(f"账号 {uname} 的cookie无效或不存在，需要初始化登录...")
            if not password:
                password = input(f"请输入账号 {uname} 的密码: ")
            try:
                get_bing_cookies(uname, password, headless=False, cookie_file=cookie_file)
            except Exception as e:
                logging.error(f"账号 {uname} 登录失败，跳过此账号。错误: {e}")
                continue
        
        # 执行任务
        devices_config = config_manager.get('devices')
        execution_config = config_manager.get('execution')
        
        if device in ['pc', 'all'] and devices_config.get('pc', {}).get('enabled', True):
            logging.info(f"账户 {uname} - 执行PC任务")
            pc_device_config = {
                'name': 'PC',
                'user_agent': devices_config['pc']['user_agent']
            }
            try:
                runner = TaskRunner(pc_device_config, execution_config, cookie_file)
                result = runner.run()
                logging.info(f"PC任务完成: {result}")
            except Exception as e:
                logging.error(f"PC任务失败: {e}")
        
        if device in ['mobile', 'all'] and devices_config.get('mobile', {}).get('enabled', True):
            logging.info(f"账户 {uname} - 执行Mobile任务")
            mobile_device_config = {
                'name': 'Mobile',
                'user_agent': devices_config['mobile']['user_agent']
            }
            try:
                runner = TaskRunner(mobile_device_config, execution_config, cookie_file)
                result = runner.run()
                logging.info(f"Mobile任务完成: {result}")
            except Exception as e:
                logging.error(f"Mobile任务失败: {e}")


def run_webui_mode(config_manager: ConfigManager):
    """WebUI模式 - 启动Web管理界面"""
    from webui import run_webui
    
    webui_config = config_manager.get('webui')
    host = webui_config.get('host', '0.0.0.0')
    port = webui_config.get('port', 5000)
    
    logging.info(f"启动WebUI模式")
    run_webui(host=host, port=port)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Microsoft Rewards 自动化工具')
    parser.add_argument('--mode', choices=['cli', 'webui'], default='cli',
                       help='运行模式: cli(命令行) 或 webui(Web界面)')
    parser.add_argument('--username', type=str, help='指定用户名（仅CLI模式）')
    parser.add_argument('--device', choices=['pc', 'mobile', 'all'], default='all',
                       help='设备类型（仅CLI模式）')
    
    args = parser.parse_args()
    
    # 初始化配置管理器（会自动创建配置文件）
    config_manager = ConfigManager()
    
    if args.mode == 'cli':
        run_cli_mode(config_manager, args.username, args.device)
    else:
        run_webui_mode(config_manager)


if __name__ == "__main__":
    main()