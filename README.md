# Microsoft-Rewards
[![version](https://img.shields.io/badge/python-3.4+-blue.svg)](https://www.python.org/download/releases/3.4.0/) 
[![status](https://img.shields.io/badge/status-stable-green.svg)](https://github.com/huaisha1224/Microsoft-Rewards)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/huaisha1224/Microsoft-Rewards)

赚取每日Microsoft Rewards积分的自动化解决方案

## 主要功能
- 通过Selenium 控制Chrome浏览器访问bing.com，完成每日的搜索任务，来获取Microsoft Rewards每日积分。
- 本项目直接操作Chrome浏览器，不需要用户提供Microsoft Rewards账户和密码，安全可靠。
- 提供API数据抓取功能，自动生成搜索关键词。

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库
- [Selenium](https://www.selenium.dev/) - 浏览器自动化
- [Requests](https://docs.python-requests.org/en/latest/) - HTTP请求
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) - 自动管理ChromeDriver（无需手动下载）
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) - 绕过自动化检测
- [pyvirtualdisplay](https://github.com/ponty/PyVirtualDisplay) - Linux下的xvfb虚拟显示支持

## 安装使用：

```sh
pip install -r requirements.txt
```

**注意：** 不再需要手动下载和配置ChromeDriver！项目现在使用webdriver-manager自动管理浏览器驱动。

### Linux用户额外依赖（可选）

如果在Linux系统下使用无头模式，建议安装xvfb以获得更好的兼容性：

```sh
# Ubuntu/Debian
sudo apt-get install xvfb

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb
```

## 使用说明

### 一键启动

运行 `main.py` 文件以启动自动化程序：

```sh
python main.py
```

### Windows版本

运行 `win.py` 文件以启动Windows版本的自动化程序：

```sh
python win.py
```

### Android版本

运行 `win-Android.py` 文件以启动Android版本的自动化程序：

```sh
python win-Android.py
```

### API数据抓取

运行 `api.py` 文件以抓取API数据并生成搜索关键词：

```sh
python api.py
```

## 备注
- 🌟 代码在Win10 + Python3.8环境中编写，如果在其他平台上运行出行问题，欢迎提issue。
- ✨ 已实现自动ChromeDriver管理，无需手动下载和配置
- 🔒 使用undetected-chromedriver技术绕过自动化检测
- 🖥️ Linux系统支持xvfb虚拟显示，实现真正的无头运行
- 🚀 优化了登录状态检测和Cookie管理机制

## 新增特性
- ✅ 自动ChromeDriver管理 - 使用webdriver-manager自动下载和更新驱动
- ✅ 反自动化检测 - 集成undetected-chromedriver绕过检测
- ✅ xvfb支持 - Linux无头模式下使用虚拟显示提高稳定性
- ✅ 增强的登录验证 - 多种方式验证登录状态，提高可靠性
- ✅ 改进的关键词获取 - 添加重试机制和备用关键词
- ✅ 优化的浏览器配置 - 更多反检测参数和性能优化

## 待完成的功能
- ~~【自动适配浏览器和ChromeDriver】~~ ✅ 已完成
- ~~【移除ChromeDriver手动配置需求】~~ ✅ 已完成  
- ~~【优化浏览器无头模式】~~ ✅ 已完成
- ~~【防止自动化识别】~~ ✅ 已完成
- 【添加定时任务功能】 
- 【添加多用户管理】
- 【兑换提醒】

![image](https://user-images.githubusercontent.com/3378350/230837253-1132c32f-30b5-4ead-9cae-70f8209ef55b.png)

