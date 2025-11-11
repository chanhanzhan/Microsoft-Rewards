#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebUI 服务器 - 提供完整的Web管理界面
"""
import os
import sys
import json
import logging
from datetime import datetime
from threading import Thread, Lock
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# 全局对象
config_manager = None
scheduler = None
execution_logs = []
execution_lock = Lock()

def init_app():
    """初始化应用"""
    global config_manager, scheduler
    
    # Import scheduler only when WebUI is used
    from scheduler import AutomationScheduler
    
    config_manager = ConfigManager()
    scheduler = AutomationScheduler(config_manager)
    
    # 如果启用自动化，启动调度器
    if config_manager.get('automation.enabled'):
        scheduler.start()
        logging.info("自动化调度器已启动")

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    return jsonify({
        "success": True,
        "config": config_manager.config
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.json
        
        # 更新配置
        for key, value in data.items():
            if '.' in key:
                config_manager.set(key, value)
            else:
                config_manager.config[key] = value
        
        config_manager.save_config()
        
        # 如果自动化配置改变，重启调度器
        if 'automation' in data:
            if config_manager.get('automation.enabled'):
                scheduler.start()
            else:
                scheduler.stop()
        
        return jsonify({
            "success": True,
            "message": "配置已更新"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """获取账户列表（包含积分信息）"""
    accounts = config_manager.get_accounts()
    # 隐藏密码，添加积分信息
    safe_accounts = []
    for acc in accounts:
        username = acc.get("username")
        safe_acc = {
            "username": username,
            "has_password": "password" in acc,
            "points": None,
            "last_updated": None
        }
        
        # 尝试从缓存获取积分信息
        cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
        if os.path.exists(cookie_file):
            safe_acc["has_cookie"] = True
        else:
            safe_acc["has_cookie"] = False
        
        safe_accounts.append(safe_acc)
    
    return jsonify({
        "success": True,
        "accounts": safe_accounts
    })

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """添加账户"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username:
            return jsonify({
                "success": False,
                "error": "用户名不能为空"
            }), 400
        
        if config_manager.add_account(username, password):
            return jsonify({
                "success": True,
                "message": f"账户 {username} 已添加"
            })
        else:
            return jsonify({
                "success": False,
                "error": "账户已存在"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accounts/<username>', methods=['DELETE'])
def delete_account(username):
    """删除账户"""
    try:
        config_manager.remove_account(username)
        
        # 同时删除cookie文件
        cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
        if os.path.exists(cookie_file):
            os.remove(cookie_file)
        
        return jsonify({
            "success": True,
            "message": f"账户 {username} 已删除"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accounts/<username>/points', methods=['GET'])
def get_account_points(username):
    """获取账户积分"""
    try:
        cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
        
        if not os.path.exists(cookie_file):
            return jsonify({
                "success": False,
                "error": "Cookie文件不存在"
            }), 404
        
        # 在后台线程查询积分，避免阻塞
        from rewards_points import get_rewards_points
        points = get_rewards_points(cookie_file)
        
        return jsonify({
            "success": True,
            "points": points
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accounts/<username>/cookie', methods=['POST'])
def refresh_account_cookie(username):
    """刷新账户Cookie"""
    try:
        # 获取账户信息
        accounts = config_manager.get_accounts()
        account = None
        for acc in accounts:
            if acc.get('username') == username:
                account = acc
                break
        
        if not account:
            return jsonify({
                "success": False,
                "error": "账户不存在"
            }), 404
        
        password = account.get('password')
        if not password:
            # 从请求中获取密码
            data = request.json or {}
            password = data.get('password')
            
            if not password:
                return jsonify({
                    "success": False,
                    "error": "需要提供密码"
                }), 400
        
        # 在后台线程刷新cookie
        def refresh_cookie():
            from scripts.cookie_manager import get_bing_cookies
            cookie_file = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
            try:
                get_bing_cookies(username, password, headless=False, cookie_file=cookie_file)
                logging.info(f"账户 {username} Cookie已刷新")
            except Exception as e:
                logging.error(f"刷新Cookie失败: {e}")
        
        thread = Thread(target=refresh_cookie)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "Cookie刷新已启动"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accounts/<username>', methods=['PUT'])
def update_account(username):
    """更新账户信息"""
    try:
        data = request.json or {}
        new_username = data.get('username', username)
        new_password = data.get('password')
        
        # 查找并更新账户
        accounts = config_manager.get_accounts()
        found = False
        for acc in accounts:
            if acc.get('username') == username:
                acc['username'] = new_username
                if new_password:
                    acc['password'] = new_password
                found = True
                break
        
        if not found:
            return jsonify({
                "success": False,
                "error": "账户不存在"
            }), 404
        
        config_manager.save_accounts(accounts)
        
        # 如果用户名改变，重命名cookie文件
        if username != new_username:
            old_cookie = os.path.join(os.path.dirname(__file__), f"cookie_{username}.txt")
            new_cookie = os.path.join(os.path.dirname(__file__), f"cookie_{new_username}.txt")
            if os.path.exists(old_cookie):
                os.rename(old_cookie, new_cookie)
        
        return jsonify({
            "success": True,
            "message": "账户已更新"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/execute', methods=['POST'])
def execute_task():
    """手动执行任务"""
    try:
        data = request.json or {}
        username = data.get('username')
        device = data.get('device', 'all')  # pc, mobile, all
        
        # 在后台线程执行任务
        def run_task():
            result = scheduler.run_manual_task(username, device)
            with execution_lock:
                execution_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "manual",
                    "username": username,
                    "device": device,
                    "result": result
                })
        
        thread = Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "任务已启动"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取执行日志"""
    with execution_lock:
        return jsonify({
            "success": True,
            "logs": execution_logs[-100:]  # 返回最近100条
        })

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    return jsonify({
        "success": True,
        "status": {
            "automation_enabled": config_manager.get('automation.enabled'),
            "scheduler_running": scheduler.is_running(),
            "next_run_time": scheduler.get_next_run_time(),
            "accounts_count": len(config_manager.get_accounts()),
            "logs_count": len(execution_logs)
        }
    })

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    try:
        scheduler.start()
        config_manager.set('automation.enabled', True)
        return jsonify({
            "success": True,
            "message": "调度器已启动"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    try:
        scheduler.stop()
        config_manager.set('automation.enabled', False)
        return jsonify({
            "success": True,
            "message": "调度器已停止"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

def add_log(log_entry):
    """添加日志条目（供外部调用）"""
    with execution_lock:
        execution_logs.append(log_entry)

def run_webui(host='0.0.0.0', port=5000):
    """运行WebUI服务器"""
    init_app()
    logging.info(f"WebUI 启动在 http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_webui()
