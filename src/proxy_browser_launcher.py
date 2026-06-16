import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from utils.UtilsLibs import LoggerManager


class ProxyBrowserLauncher(QThread):
    """
    用于启动浏览器的后台线程，防止UI卡顿。
    """
    launch_finished = pyqtSignal(bool, str)

    def __init__(self, logger: LoggerManager, proxy_host, proxy_port, proxy_protocol, homepage_url, browser_path, user_data_dir):
        super().__init__()
        self.logger = logger
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_protocol = proxy_protocol
        self.homepage_url = homepage_url
        self.browser_path = browser_path
        self.user_data_dir = os.path.expandvars(user_data_dir)

        self.logger.debug(
            f"初始化浏览器启动线程 - 代理: {proxy_protocol}://{proxy_host}:{proxy_port}, 浏览器路径: {self.browser_path}, 用户数据目录: {self.user_data_dir}")

    def run(self):
        # 构建启动参数：代理服务器 + 用户数据目录
        if self.proxy_protocol == "http":
            proxy_arg = f"--proxy-server=http://{self.proxy_host}:{self.proxy_port}"
        else:  # 默认使用socks5
            proxy_arg = f"--proxy-server=socks5://{self.proxy_host}:{self.proxy_port}"
        user_data_arg = f"--user-data-dir={self.user_data_dir}"

        # 构建完整的浏览器启动命令列表
        cmd_args = [self.browser_path, proxy_arg, user_data_arg]

        # 配置了主页URL
        if self.homepage_url:
            cmd_args.append(self.homepage_url)
            self.logger.debug(f"配置了浏览器主页: {self.homepage_url}")
        else:
            self.logger.debug("未配置浏览器主页，将使用浏览器默认设置")

        try:
            # 确保用户数据目录存在
            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir)
                self.logger.info(f"创建用户数据目录: {self.user_data_dir}")

            # 启动浏览器
            self.logger.info(f"启动浏览器: {' '.join(cmd_args)}")
            subprocess.Popen(cmd_args)
            self.launch_finished.emit(True, "浏览器已启动。")
            self.logger.info("浏览器启动成功")
        except FileNotFoundError:
            error_msg = f"未找到浏览器程序: {self.browser_path}"
            self.logger.error(error_msg)
            self.launch_finished.emit(False, error_msg)
        except Exception as e:
            error_msg = f"启动浏览器时出错: {repr(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.launch_finished.emit(False, error_msg)
