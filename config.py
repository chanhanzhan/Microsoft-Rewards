#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块 - 自动初始化配置文件
"""
import os
import json
from typing import Dict, Any

class ConfigManager:
    """配置管理器 - 负责配置文件的加载、保存和初始化"""
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "automation": {
            "enabled": False,
            "mode": "random_24h",  # random_24h: 24小时内随机运行, fixed: 固定时间运行
            "first_run_on_start": True,
            "timezone": "Asia/Shanghai"
        },
        "execution": {
            "max_search_count": 50,
            "simulate_typing": True,
            "headless": False,
            "base_delay": [1, 15],
            "retry_delay": 5,
            "max_retries": 3
        },
        "devices": {
            "pc": {
                "enabled": True,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
            },
            "mobile": {
                "enabled": True,
                "user_agent": "Mozilla/5.0 (Linux; Android 14; 23078RKD5C Build/UP1A.230905.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36"
            }
        },
        "webui": {
            "enabled": True,
            "host": "0.0.0.0",
            "port": 5000,
            "websocket_port": 5001
        }
    }
    
    DEFAULT_ACCOUNTS = []
    
    def __init__(self, config_dir: str = None):
        """初始化配置管理器"""
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.accounts_file = os.path.join(config_dir, "account.json")
        
        # 自动初始化配置文件
        self.config = self._load_or_create_config()
        self.accounts = self._load_or_create_accounts()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """加载或创建配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(f"已加载配置文件: {self.config_file}")
                # 合并默认配置（确保新配置项存在）
                return self._merge_config(self.DEFAULT_CONFIG, config)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                return self.DEFAULT_CONFIG.copy()
        else:
            print(f"配置文件不存在，创建默认配置: {self.config_file}")
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _load_or_create_accounts(self) -> list:
        """加载或创建账户文件"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, "r", encoding="utf-8") as f:
                    accounts = json.load(f)
                print(f"已加载账户文件: {self.accounts_file} ({len(accounts)} 个账户)")
                return accounts
            except Exception as e:
                print(f"加载账户文件失败: {e}")
                return self.DEFAULT_ACCOUNTS.copy()
        else:
            print(f"账户文件不存在，创建空账户文件: {self.accounts_file}")
            self.save_accounts(self.DEFAULT_ACCOUNTS)
            return self.DEFAULT_ACCOUNTS.copy()
    
    def _merge_config(self, default: Dict, current: Dict) -> Dict:
        """递归合并配置，确保所有默认键存在"""
        result = current.copy()
        for key, value in default.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_config(value, result[key])
        return result
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存: {self.config_file}")
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def save_accounts(self, accounts: list = None):
        """保存账户到文件"""
        if accounts is None:
            accounts = self.accounts
        
        try:
            with open(self.accounts_file, "w", encoding="utf-8") as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            print(f"账户已保存: {self.accounts_file}")
        except Exception as e:
            print(f"保存账户失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的键）"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值（支持点号分隔的键）"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def add_account(self, username: str, password: str = None):
        """添加账户"""
        account = {"username": username}
        if password:
            account["password"] = password
        
        # 检查是否已存在
        for acc in self.accounts:
            if acc.get("username") == username:
                print(f"账户 {username} 已存在")
                return False
        
        self.accounts.append(account)
        self.save_accounts()
        print(f"已添加账户: {username}")
        return True
    
    def remove_account(self, username: str):
        """删除账户"""
        self.accounts = [acc for acc in self.accounts if acc.get("username") != username]
        self.save_accounts()
        print(f"已删除账户: {username}")
    
    def get_accounts(self) -> list:
        """获取所有账户"""
        return self.accounts


if __name__ == "__main__":
    # 测试配置管理器
    config_manager = ConfigManager()
    print("\n当前配置:")
    print(json.dumps(config_manager.config, ensure_ascii=False, indent=2))
    print("\n当前账户:")
    print(json.dumps(config_manager.accounts, ensure_ascii=False, indent=2))
