#!/usr/bin/env python
import subprocess
import sys
import platform
import os
import json
from scripts.cookie_manager import is_cookie_valid, get_bing_cookies

def get_accounts():
    account_path = os.path.join(os.path.dirname(__file__), "account.json")
    if not os.path.exists(account_path):
        print("未检测到账户文件，请先初始化账号信息（account.json）！")
        sys.exit(1)
    with open(account_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not data:
            print("账号文件为空，请先添加账号信息！")
            sys.exit(1)
        return data

def run_script(script_name, env=None):
    try:
        subprocess.run([sys.executable, script_name], check=True, env=env)
    except subprocess.CalledProcessError:
        sys.exit(1)

if __name__ == "__main__":
    # 启动 api.py 脚本
    run_script("api.py")

    accounts = get_accounts()
    base_dir = os.path.join(os.path.dirname(__file__), "scripts")
    for account in accounts:
        username = account["username"]
        password = account.get("password")
        cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
        # 检查 cookie 是否有效，否则重新获取
        if not is_cookie_valid(username=username, cookie_file=cookie_file):
            print(f"账号 {username} 的cookie无效或不存在，需要初始化登录...")
            if not password:
                password = input(f"请输入账号 {username} 的密码: ")
            try:
                get_bing_cookies(username, password, headless=False, cookie_file=cookie_file)
            except Exception as e:
                print(f"账号 {username} 登录失败，跳过此账号。错误: {e}")
                continue
        # 运行各脚本时传递 cookie 文件名
        env = os.environ.copy()
        env["COOKIE_FILE"] = cookie_file
        if platform.system() == "Windows":
            run_script(os.path.join(base_dir, "win.py"), env=env)
            run_script(os.path.join(base_dir, "win-Android.py"), env=env)
        elif platform.system() == "Linux":
            run_script(os.path.join(base_dir, "linux.py"), env=env)
            run_script(os.path.join(base_dir, "linux-Android.py"), env=env)