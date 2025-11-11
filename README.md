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
- **🆕 模块化任务系统** - 支持PC和移动设备的独立配置和执行
- **🆕 配置自动初始化** - 首次运行自动创建配置文件
- **🆕 WebUI管理界面** - 完整的Web管理界面，支持账户管理、配置管理、任务执行和日志查看
- **🆕 自动化调度** - 24小时内随机运行，首次运行后自动循环
- **🆕 完整数据展示** - 实时显示执行状态、日志和统计信息

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库
- [Selenium](https://www.selenium.dev/) - 浏览器自动化
- [Requests](https://docs.python-requests.org/en/latest/) - HTTP请求
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) - 自动管理ChromeDriver（无需手动下载）
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) - 绕过自动化检测
- [pyvirtualdisplay](https://github.com/ponty/PyVirtualDisplay) - Linux下的xvfb虚拟显示支持
- [Flask](https://flask.palletsprojects.com/) - Web框架

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

### 🌟 WebUI模式（推荐）

启动Web管理界面，通过浏览器进行所有配置和管理：

```sh
python main.py --mode webui
```

然后在浏览器中访问 `http://localhost:5000`

Web界面功能：
- 📊 **仪表盘** - 查看系统状态、账户数量、下次运行时间
- 👥 **账户管理** - 添加、删除、管理多个Microsoft账户
- ⚙️ **配置管理** - 设置自动化、执行参数、设备配置
- ▶️ **手动执行** - 手动触发指定账户和设备的任务
- 📝 **执行日志** - 查看详细的执行历史和结果

### 命令行模式

执行所有账户的所有设备任务：

```sh
python main.py --mode cli
```

执行指定账户的任务：

```sh
python main.py --mode cli --username your_account@example.com
```

执行指定设备的任务：

```sh
python main.py --mode cli --device pc      # 仅PC
python main.py --mode cli --device mobile  # 仅移动设备
```

### 配置文件

首次运行时，程序会自动创建以下配置文件：

- `config.json` - 主配置文件（自动化、执行参数、设备配置）
- `account.json` - 账户配置文件

示例文件已提供：
- `config.json.example` - 配置示例
- `account.json.example` - 账户配置示例

### 自动化调度

在配置文件中启用自动化：

```json
{
  "automation": {
    "enabled": true,
    "mode": "random_24h",
    "first_run_on_start": true
  }
}
```

或通过WebUI界面启用。

自动化特性：
- 首次启动时立即运行（可配置）
- 每24小时内随机选择一个时间运行
- 自动管理每日运行计数
- 跨时区支持

### API数据抓取

运行 `api.py` 文件以抓取API数据并生成搜索关键词：

```sh
python api.py
```

## 新增特性 v2.0

### ✅ 模块化架构
- **配置管理** (`config.py`) - 统一的配置管理，支持自动初始化
- **任务执行器** (`task_runner.py`) - 统一的任务执行模块，支持设备参数
- **自动化调度器** (`scheduler.py`) - 智能调度系统，24小时随机执行

### ✅ WebUI管理界面
- **现代化界面** - 响应式设计，支持移动端访问
- **实时状态** - 自动刷新系统状态和执行进度
- **账户管理** - 图形化添加、删除、管理账户
- **配置管理** - 可视化配置所有参数
- **日志查看** - 实时查看执行日志和历史记录

### ✅ 设备管理
- **独立配置** - PC和移动设备独立的User-Agent和参数
- **灵活执行** - 可选择性执行PC、移动或全部设备
- **统一接口** - 通过相同的API执行不同设备的任务

### ✅ 自动化调度
- **随机执行** - 24小时内随机时间执行，避免检测
- **首次运行** - 启动时立即运行（可配置）
- **日期管理** - 自动跟踪每日执行状态
- **容错机制** - 失败重试和异常处理

## 项目结构

```
Microsoft-Rewards/
├── main.py              # 主入口，支持CLI和WebUI模式
├── config.py            # 配置管理模块
├── task_runner.py       # 任务执行器
├── scheduler.py         # 自动化调度器
├── webui.py            # WebUI服务器
├── api.py              # 关键词获取
├── config.json         # 配置文件（自动生成）
├── account.json        # 账户文件（自动生成）
├── templates/          # HTML模板
│   └── index.html      # WebUI主界面
├── scripts/            # 原有脚本（保留兼容性）
│   ├── cookie_manager.py
│   ├── win.py
│   ├── linux.py
│   └── ...
└── requirements.txt    # 依赖包列表
```

## 备注
- 🌟 代码在Win10 + Python3.8环境中编写，如果在其他平台上运行出现问题，欢迎提issue。
- ✨ 已实现自动ChromeDriver管理，无需手动下载和配置
- 🔒 使用undetected-chromedriver技术绕过自动化检测
- 🖥️ Linux系统支持xvfb虚拟显示，实现真正的无头运行
- 🚀 优化了登录状态检测和Cookie管理机制
- 🎯 模块化设计，易于扩展和维护
- 🌐 完整的WebUI管理界面，操作更便捷
- ⏰ 智能调度系统，自动化执行任务

## 已完成的功能
- ✅ 【自动适配浏览器和ChromeDriver】
- ✅ 【移除ChromeDriver手动配置需求】  
- ✅ 【优化浏览器无头模式】
- ✅ 【防止自动化识别】
- ✅ 【添加定时任务功能】
- ✅ 【添加多用户管理】
- ✅ 【模块化任务系统】
- ✅ 【配置自动初始化】
- ✅ 【WebUI管理界面】
- ✅ 【自动化调度】
- ✅ 【完整数据展示】

## 待完成的功能
- 【兑换提醒】
- 【更多自定义调度模式】
- 【邮件通知】

![image](https://user-images.githubusercontent.com/3378350/230837253-1132c32f-30b5-4ead-9cae-70f8209ef55b.png)

