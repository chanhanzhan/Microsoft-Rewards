import requests
import re
import os

def clean_keyword(word):
    # 只保留中文、英文、数字和空格
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9 ]', '', word)

def fetch_keywords_from_weibo():
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"获取微博热搜失败: {e}")
        return

    keywords = set()

    try:
        # 提取 data.realtime 中所有 note 字段
        realtime_list = data.get("data", {}).get("realtime", [])
        for item in realtime_list:
            note = item.get("note")
            if note:
                clean = clean_keyword(note.strip())
                if clean:
                    keywords.add(clean)
    except Exception as e:
        print(f"数据结构解析失败: {e}")
        return

    if not keywords:
        print("未获取到任何关键词！")
        return

    with open("keyword.txt", "w", encoding="utf-8") as f:
        for kw in sorted(keywords):
            f.write(kw + "\n")

    print(f"已写入 {len(keywords)} 个关键词到 keyword.txt")

if __name__ == "__main__":
    fetch_keywords_from_weibo()
