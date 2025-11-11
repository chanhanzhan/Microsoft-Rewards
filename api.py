import requests
import re
import os
import random
import time

def clean_keyword(word):
    # 只保留中文、英文、数字和空格
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9 ]', '', word)

def fetch_keywords_from_weibo():
    """从微博获取热搜关键词"""
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/",
        "Accept": "application/json",
    }

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            keywords = set()
            # 提取 data.realtime 中所有 note 字段
            realtime_list = data.get("data", {}).get("realtime", [])
            for item in realtime_list:
                note = item.get("note")
                if note:
                    clean = clean_keyword(note.strip())
                    if clean:
                        keywords.add(clean)
            
            if keywords:
                with open("keyword.txt", "w", encoding="utf-8") as f:
                    for kw in sorted(keywords):
                        f.write(kw + "\n")
                print(f"已写入 {len(keywords)} 个关键词到 keyword.txt")
                return True
            else:
                print(f"尝试 {attempt + 1}/{max_retries}: 未获取到任何关键词！")
                
        except requests.RequestException as e:
            print(f"尝试 {attempt + 1}/{max_retries}: 获取微博热搜失败: {e}")
        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries}: 数据结构解析失败: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (attempt + 1))  # 指数退避
    
    print("多次尝试后仍未成功获取关键词，使用备用关键词")
    return False

def generate_fallback_keywords():
    """生成备用关键词"""
    fallback_keywords = [
        "新闻", "科技", "体育", "娱乐", "财经", "汽车", "房产", "时尚",
        "教育", "健康", "旅游", "美食", "游戏", "音乐", "电影", "书籍",
        "天气", "股票", "足球", "篮球", "手机", "电脑", "笔记本", "相机",
        "手表", "耳机", "键盘", "鼠标", "显示器", "打印机"
    ]
    
    # 添加一些随机组合
    random.shuffle(fallback_keywords)
    selected = fallback_keywords[:20]
    
    with open("keyword.txt", "w", encoding="utf-8") as f:
        for kw in selected:
            f.write(kw + "\n")
    
    print(f"已写入 {len(selected)} 个备用关键词到 keyword.txt")

if __name__ == "__main__":
    if not fetch_keywords_from_weibo():
        generate_fallback_keywords()
