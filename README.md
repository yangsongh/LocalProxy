# LocalProxy - 智能代理工具

[![Version](https://img.shields.io/badge/version-202606171-blue.svg)](https://github.com/yangsongh/LocalProxy)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

> 一款轻量级的智能代理管理工具，自动扫描、激活并启动代理服务，让上网更便捷。

---

## 📖 项目简介

**LocalProxy** 是一款专为局域网环境设计的代理管理工具，能够自动从管理员设备拉取配置、扫描可用代理服务器，并一键启动配置好代理的浏览器。无论是教室、办公室还是实验室场景，LocalProxy 都能帮助用户快速接入网络。

项目采用客户端-服务器架构，客户端自动从管理员设备获取最新的代理服务器列表和配置信息，支持 SOCKS5 和 HTTP 代理协议，并提供激活授权、版本更新等完整的企业级功能。

### 核心应用场景

- 🏫 **校园机房**：学生端自动获取代理配置，无需手动设置
- 🏢 **企业内网**：统一管理和分发代理服务器信息
- 🧪 **实验室环境**：快速切换和测试不同代理服务器

---

## ✨ 功能特性

| 功能                   | 说明                                                   |
| ---------------------- | ------------------------------------------------------ |
| 🔄 **自动配置拉取**    | 启动时自动从管理员设备获取最新代理配置，无需手动配置   |
| 🔍 **智能代理扫描**    | 多线程并发扫描代理服务器，自动检测可用性和响应延迟     |
| 🚀 **一键启动浏览器**  | 选中代理服务器后一键启动已配置代理的浏览器             |
| 🔐 **设备激活机制**    | 基于硬盘序列号的设备绑定，支持设备ID自动上报和远程激活 |
| 🔑 **设备密码保护**    | 支持为特定设备设置访问密码，保护未授权使用             |
| 📦 **自动更新**        | 内置更新器，支持从远程服务器下载并解压更新包           |
| 📊 **直观的 GUI 界面** | 基于 PyQt5 开发的桌面应用，操作简单直观                |
| 🛡️ **配置加密存储**    | 使用 Fernet 对称加密保护本地配置文件                   |
| 🗂️ **日志记录系统**    | 完善的日志记录，支持控制台彩色输出和文件持久化         |
| 🔒 **单实例运行**      | 防止程序重复启动，避免资源冲突                         |

---

## 🛠️ 技术栈

| 类别         | 技术                                     |
| ------------ | ---------------------------------------- |
| **编程语言** | Python 3.8+                              |
| **GUI 框架** | PyQt5                                    |
| **网络请求** | Requests, PySocks                        |
| **系统交互** | WMI (Windows Management Instrumentation) |
| **加密库**   | cryptography (Fernet)                    |
| **日志系统** | colorlog, logging                        |
| **打包工具** | PyInstaller, Inno Setup                  |
| **并发处理** | ThreadPoolExecutor, QThread              |

---

## 📋 前置条件

- **操作系统**：Windows 7/10/11 (64位)
- **Python 版本**：Python 3.8 或更高版本
- **包管理工具**：pip

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yangsongh/LocalProxy.git
cd LocalProxy
```

### 2. 创建虚拟环境 (推荐)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置说明

在运行前，请确保 `src/config_manager.py` 中的管理员 IP 列表配置正确：

```python
ADMIN_IPS = [
    "172.16.192.1",    # 电视盒子
    "172.16.194.149",  # 13班备用 (管控状态)
    "172.16.194.91",   # 13班备用 (开网状态)
    "172.16.114.21",   # 15班
    "localhost"        # 本地开发
]
```

### 5. 运行程序

```bash
python src/main.py
```

### 6. 构建可执行文件

使用提供的构建脚本：

```batch
BUILD.BAT
```

或手动使用 PyInstaller：

```bash
pyinstaller -D -w --distpath build --workpath %PYINSTALLER_CACHE_DIR% -i assets\icon.ico -n LocalProxy --noconfirm src/main.py
```

---

## 📁 项目结构

```
LocalProxy/
├── src/                          # 源代码目录
│   ├── main.py                   # 程序入口，主窗口逻辑
│   ├── config_manager.py         # 配置管理 (拉取、加载、加密、激活)
│   ├── server_scanner.py         # 代理服务器扫描器 (多线程)
│   ├── proxy_browser_launcher.py # 浏览器启动线程
│   ├── updater.py                # 自动更新器 (Tkinter GUI)
│   └── utils/
│       └── UtilsLibs.py          # 通用工具库 (日志、异常处理、DPI适配)
├── build_scripts/                # 构建脚本
│   ├── script.iss                # Inno Setup 安装脚本
│   └── welcome.txt               # 安装欢迎信息
├── assets/                       # 资源文件
│   └── icon.ico                  # 程序图标
├── .vscode/                      # VSCode 配置
│   ├── launch.json               # 调试配置
│   └── settings.json             # 编辑器设置
├── requirements.txt              # Python 依赖列表
├── BUILD.BAT                     # Windows 构建批处理脚本
├── LocalProxy.spec               # PyInstaller 规格文件
├── Updater.spec                  # Updater PyInstaller 规格文件
└── LICENSE                       # MIT 许可证
```

### 核心模块说明

| 模块                        | 功能描述                                                   |
| --------------------------- | ---------------------------------------------------------- |
| `config_manager.py`         | 从管理员设备拉取配置、加密存储、设备激活状态检查、密码验证 |
| `server_scanner.py`         | 多线程扫描代理服务器，支持 SOCKS5 和 HTTP 协议检测         |
| `proxy_browser_launcher.py` | 在后台线程中启动带代理配置的浏览器                         |
| `updater.py`                | 独立的自动更新程序，支持下载和解压更新包                   |
| `UtilsLibs.py`              | 日志管理、异常捕获、DPI适配、单实例检测等通用功能          |

---

## ⚙️ 配置说明

### 管理员服务器 API 端点

| 端点                                        | 方法 | 说明                         |
| ------------------------------------------- | ---- | ---------------------------- |
| `/localproxy/get_config?ver={VERSION_CODE}` | GET  | 获取最新配置，传入当前版本号 |
| `/localproxy/post_activate`                 | POST | 上报设备ID用于激活           |

### 配置数据结构

```json
{
  "proxy_servers": ["socks5://192.168.1.100:1080", "http://192.168.1.101:8080"],
  "browser": {
    "test_url": "http://example.com/test",
    "browser_homepage": "https://example.com",
    "browser_path": "C:\\Program Files\\...\\msedge.exe",
    "user_data_dir": "%USERPROFILE%\\...\\User Data"
  },
  "activated_devices_passwords": {
    "DISK_SERIAL_123": "password123"
  },
  "expiry_date": "2026-12-31 23:59:59",
  "version": {
    "latest_vercode": 202606171,
    "force_update": true,
    "update_content": "修复了若干问题",
    "update_url": "https://example.com/download",
    "auto_update": true,
    "zip_url": "https://example.com/update.zip",
    "zip_pwd": "password",
    "extract_path": "%APPDATA%\\LocalProxy"
  }
}
```

### 环境变量

| 变量                    | 说明                              |
| ----------------------- | --------------------------------- |
| `PYTHON_VENV_DIR`       | 虚拟环境目录 (用于 VSCode 配置)   |
| `PYINSTALLER_CACHE_DIR` | PyInstaller 缓存目录 (构建时使用) |

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！请遵循以下流程：

### 1. Fork 本仓库

### 2. 创建特性分支

```bash
git checkout -b feature/amazing-feature
```

### 3. 提交代码

```bash
git commit -m 'Add some amazing feature'
```

### 4. 推送到分支

```bash
git push origin feature/amazing-feature
```

### 5. 提交 Pull Request

### 代码规范

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范
- 使用类型注解 (Type Hints) 提高代码可读性
- 为新增功能编写必要的注释和文档字符串
- 确保所有测试通过

### 本地开发环境

1. 克隆仓库并安装依赖
2. 使用 VSCode 打开项目，配置已包含在 `.vscode/` 目录中
3. 调试配置已预设，按 `F5` 即可启动调试

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 进行许可。您可以自由使用、修改和分发本软件，但需保留版权声明。

---

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 GUI 框架
- [PyInstaller](https://pyinstaller.org/) - Python 应用打包工具
- [Inno Setup](https://jrsoftware.org/isinfo.php) - Windows 安装程序制作工具

---

## 📞 联系方式

- 提交 [GitHub Issue](https://github.com/yangsongh/LocalProxy/issues)
- 邮件联系：18675864731@163.com

---
