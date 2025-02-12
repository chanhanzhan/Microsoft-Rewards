import json
import os
import requests
import random

def extract_info(data, key_list, exclude_keywords):
    results = {'titles': set(), 'points': {}}
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'title' and isinstance(value, str):
                if not any(keyword in value for keyword in exclude_keywords):
                    results['titles'].add(value)
            elif key in key_list:
                results['points'][key] = value
            elif isinstance(value, (dict, list)):
                sub_results = extract_info(value, key_list, exclude_keywords)
                results['titles'].update(sub_results['titles'])
                results['points'].update(sub_results['points'])  # 修复了这个错误，缺少了右括号
    
    elif isinstance(data, list):
        for item in data:
            sub_results = extract_info(item, key_list, exclude_keywords)
            results['titles'].update(sub_results['titles'])
            results['points'].update(sub_results['points'])

    return results

def load_cookies_from_file(cookie_path):
    cookies = []
    
    if not os.path.exists(cookie_path):
        print(f"Cookie 文件 {cookie_path} 不存在！")
        return cookies

    with open(cookie_path, "r", encoding="utf-8") as f:
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
    return cookies

def fetch_and_parse_api_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_path = os.path.join(current_dir, "cookie.txt")

    cookies = load_cookies_from_file(cookie_path)
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    cookie_jar = requests.cookies.RequestsCookieJar()
    for cookie in cookies:
        cookie_jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"], secure=cookie["secure"])

    url = 'https://rewards.bing.com/api/getuserinfo'
    headers = {
        'Referer': 'https://rewards.bing.com/?publ=BingMobile&crea=MOBILE',
        'X-Requested-With': 'XMLHttpRequest'
    }
    response = requests.get(url, headers=headers, cookies=cookie_jar)
    headers = {
        'Referer': 'https://rewards.bing.com/?publ=BingMobile&crea=MOBILE',
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = requests.get(url, headers=headers, cookies=cookie_dict)

    if response.status_code == 200:
        print("请求成功，开始解析返回数据...")

        try:
            json_data = response.json()  # 直接解析响应数据为 JSON
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return

        # 定义查找的键和排除的标题关键词
        keys_to_find = ['lifetimePoints', 'availablePoints']
        exclude_keywords = ['可兑','优惠券', '抽奖机', '电脑搜索','免费', '数字金币', '活动', '打分', '兑换', '码', '元',"当日连续","连续奖励","200","user","拼图","答案","套装","Office","充值","GAP","day","礼品卡","捐款","抽奖","World","爱心","boss","of","Local","Sweetheart","Audiofile","Founder"]

        # 提取信息
        extracted_info = extract_info(json_data, keys_to_find, exclude_keywords)

        # 美化输出
        print("提取的信息如下：\n")

        if extracted_info['titles']:
            # 将标题写入到 keyword.txt 文件
            with open('keyword.txt', 'w', encoding='utf-8') as keyword_file:
                for title in sorted(extracted_info['titles']):
                    keyword_file.write(title + "\n")

        if extracted_info['points']:
            lifetime_points = extracted_info['points'].get('lifetimePoints', '未找到')
            print(f"\n积分数量: {lifetime_points}")

        # 从 word.txt 中获取随机数据补充标题
        add_random_titles_from_word_txt()

    else:
        print(f"请求失败，状态码：{response.status_code}")

def add_random_titles_from_word_txt():
    # 读取 word.txt 文件中的数据
    if not os.path.exists("word.txt"):
        print("word.txt 文件不存在，无法获取随机数据！")
        return
    
    with open("word.txt", "r", encoding="utf-8") as file:
        word_list = file.readlines()

    # 去除空行和多余的空格
    word_list = [word.strip() for word in word_list if word.strip()]

    if len(word_list) < 1:
        print("word.txt 文件内容为空，无法生成随机标题！")
        return

    # 从 word.txt 中随机选择若干个标题补充到 keyword.txt
    with open("keyword.txt", "a", encoding="utf-8") as keyword_file:
        current_titles = set()
        
        # 读取现有的 keyword.txt 中的标题
        with open("keyword.txt", "r", encoding="utf-8") as existing_file:
            current_titles.update(existing_file.readlines())
        
        # 计算需要补充的标题数量
        remaining_titles_to_add = 30- len(current_titles)
        if remaining_titles_to_add > 0:
            # 随机选择剩余标题
            selected_titles = random.sample(word_list, min(remaining_titles_to_add, len(word_list)))
            
            # 添加到 keyword.txt
            for title in selected_titles:
                if title.strip() and title + "\n" not in current_titles:  # 确保标题非空
                    keyword_file.write(title + "\n")

if __name__ == "__main__":
    fetch_and_parse_api_data()