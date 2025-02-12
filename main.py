#!/usr/bin/env python
import subprocess
import sys
import platform

def run_script(script_name):
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

if __name__ == "__main__":
    # 启动 api.py 脚本
    run_script("api.py")
    
    # 根据操作系统运行不同的脚本
    if platform.system() == "Windows":
        run_script("win.py")
        run_script("win-Android.py")
    elif platform.system() == "Linux":
        run_script("linux.py")
        run_script("linux-Android.py")