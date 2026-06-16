import os
import sys
import webbrowser
import subprocess

from server_scanner import ServerScanner
from config_manager import ConfigManager, VERSION_CODE
from proxy_browser_launcher import ProxyBrowserLauncher
from utils.UtilsLibs import LoggerManager, Utils

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QHeaderView,
    QDesktopWidget,
)


class SplashWindow(QWidget):
    """极简启动界面"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.center_window()

    def init_ui(self):
        self.setWindowTitle(f"启动中")
        self.setFixedSize(280, 150)

        layout = QVBoxLayout()
        label = QLabel(f"正在更新配置...\n当前版本号: {VERSION_CODE}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore
        label.setStyleSheet("font-size: 16px;")
        layout.addWidget(label)

        self.setLayout(layout)

    def center_window(self):
        """将窗口移动到屏幕中央"""
        screen_geometry = QDesktopWidget().screenGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())


class MainWindow(QMainWindow):
    """程序主窗口"""

    def __init__(self, logger: LoggerManager, config_manager):
        super().__init__()
        self.logger = logger
        self.config_manager = config_manager

        self.setWindowTitle(f"上网工具 (版本号{VERSION_CODE})")
        self.resize(430, 320)
        self.center_window()
        self.init_ui()

        self.scanner_thread = None
        self.launcher_thread = None

        self.is_auto_scan = True  # 默认是自动扫描
        QTimer.singleShot(0, lambda: self.start_scan(auto_scan=True))  # 自动启动扫描

    def center_window(self):
        """将窗口移动到屏幕中央"""
        screen_geometry = QDesktopWidget().screenGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def init_ui(self):
        self.logger.info("初始化主窗口")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(self.status_label)

        # 服务器列表表格
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(
            ["IP地址", "端口", "协议", "响应时间 (ms)"])
        self.server_table.horizontalHeader().setSectionResizeMode(  # type: ignore
            QHeaderView.Stretch)

        self.server_table.setSelectionBehavior(
            QTableWidget.SelectRows)  # 点击后直接选择整行
        self.server_table.setSelectionMode(
            QTableWidget.SingleSelection)  # 只允许同时选中一行
        self.server_table.setEditTriggers(
            QTableWidget.NoEditTriggers)  # 禁止用户编辑表格内容

        main_layout.addWidget(self.server_table)

        # 按钮布局 - 将扫描和打开浏览器按钮放在同一排
        button_layout = QHBoxLayout()

        # 扫描按钮
        self.scan_button = QPushButton("扫描服务器")
        self.scan_button.clicked.connect(self.start_scan)
        button_layout.addWidget(self.scan_button)

        # 打开浏览器按钮
        self.open_edge_btn = QPushButton("打开浏览器")
        self.open_edge_btn.clicked.connect(self.launch_browser)
        self.open_edge_btn.setEnabled(False)  # 初始禁用，直到扫描完成
        button_layout.addWidget(self.open_edge_btn)

        main_layout.addLayout(button_layout)

    def start_scan(self, auto_scan=False):
        """
        启动服务器扫描。

        Args:
            auto_scan: True表示自动扫描，False表示手动扫描
        """
        test_url = self.config_manager.data["browser"]["test_url"]
        servers = self.config_manager.data.get("proxy_servers", [])
        if not servers:
            self.logger.warning("用户尝试扫描但配置中没有代理服务器列表")
            QMessageBox.warning(self, "警告", "配置中没有代理服务器列表！")
            return

        self.scan_button.setEnabled(False)
        self.open_edge_btn.setEnabled(False)
        self.status_label.setText("正在扫描...")

        # 记录扫描类型
        self.is_auto_scan = auto_scan
        self.logger.debug(
            f"开始{'自动' if auto_scan else '手动'}扫描，服务器数量: {len(servers)}")

        # 创建并启动扫描线程
        self.scanner_thread = ServerScanner(self.logger, servers, test_url)
        self.scanner_thread.scan_finished.connect(self.on_scan_finished)
        self.scanner_thread.update_status.connect(
            self.status_label.setText)
        self.scanner_thread.start()

    def on_scan_finished(self, results):
        """扫描线程完成后的回调函数"""
        self.scan_button.setEnabled(True)

        if not results:
            self.logger.info("扫描完成，但未找到可用服务器")
            self.status_label.setText("扫描完成，但未找到可用的服务器。")
            self.open_edge_btn.setEnabled(False)
            self.server_table.setRowCount(0)  # 清空表格，显示无数据
            return

        # 按响应时间排序
        results.sort(key=lambda x: x['latency'])

        # 填充表格
        self.server_table.setRowCount(len(results))
        for row, server in enumerate(results):
            # 创建单元格并设置对齐方式
            item_ip = QTableWidgetItem(server['ip'])
            item_ip.setTextAlignment(Qt.AlignCenter)  # type: ignore # 设置居中对齐

            item_port = QTableWidgetItem(str(server['port']))
            item_port.setTextAlignment(Qt.AlignCenter)  # type: ignore # 设置居中对齐

            item_protocol = QTableWidgetItem(str(server['protocol']))
            item_protocol.setTextAlignment(
                Qt.AlignCenter)  # type: ignore # 设置居中对齐

            item_latency = QTableWidgetItem(str(server['latency']))
            item_latency.setTextAlignment(
                Qt.AlignCenter)  # type: ignore # 设置居中对齐

            # 将单元格添加到表格
            self.server_table.setItem(row, 0, item_ip)
            self.server_table.setItem(row, 1, item_port)
            self.server_table.setItem(row, 2, item_protocol)
            self.server_table.setItem(row, 3, item_latency)

        # 默认选中第一个（响应时间最短的）
        self.server_table.selectRow(0)
        self.open_edge_btn.setEnabled(True)
        self.status_label.setText(
            f'扫描完成，找到 {len(results)} 个服务器。请选择并点击"打开浏览器"。')
        self.logger.info(f"扫描结果已填充到表格，共 {len(results)} 个可用服务器")

        QTimer.singleShot(0, self.auto_launch_browser)

    def _launch_browser_with_server(self, host, port, protocol):
        """公共的浏览器启动逻辑"""
        # 获取配置中的浏览器主页URL
        homepage_url = self.config_manager.data['browser']['browser_homepage']
        browser_path = self.config_manager.data['browser']['browser_path']
        user_data_dir = self.config_manager.data['browser']['user_data_dir']

        self.open_edge_btn.setEnabled(False)
        self.status_label.setText(
            f"正在启动浏览器，代理: {protocol}://{host}:{port} ...")

        # 创建并启动浏览器启动线程
        self.launcher_thread = ProxyBrowserLauncher(
            self.logger, host, port, protocol, homepage_url, browser_path, user_data_dir)
        self.launcher_thread.launch_finished.connect(self.on_launch_finished)
        self.launcher_thread.start()

    def auto_launch_browser(self):
        """扫描完成后自动启动浏览器"""
        # 只有自动扫描才自动启动浏览器
        if self.is_auto_scan:
            # 检查是否有可用服务器
            if self.server_table.rowCount() > 0:
                self.logger.info("自动扫描到可用服务器，开始自动启动浏览器")

                # 获取第一个服务器（延迟最低的）
                host = self.server_table.item(0, 0).text()  # type: ignore
                port = self.server_table.item(0, 1).text()  # type: ignore
                protocol = self.server_table.item(0, 2).text()  # type: ignore

                # 调用公共的启动方法
                self._launch_browser_with_server(host, port, protocol)
            else:
                self.logger.info("自动扫描没有找到可用服务器，不自动启动浏览器")
        else:
            self.logger.debug("手动扫描完成，不自动启动浏览器")

    def launch_browser(self):
        """启动浏览器"""
        selected_rows = self.server_table.selectionModel().selectedRows()  # type: ignore
        if not selected_rows:
            self.logger.warning("用户尝试启动浏览器但未选择代理服务器")
            QMessageBox.warning(self, "警告", "请先从列表中选择一个代理服务器。")
            return

        row = selected_rows[0].row()
        host = self.server_table.item(row, 0).text()  # type: ignore
        port = self.server_table.item(row, 1).text()  # type: ignore
        protocol = self.server_table.item(row, 2).text()  # type: ignore

        # 调用公共的启动方法
        self._launch_browser_with_server(host, port, protocol)

    def on_launch_finished(self, success, message):
        """浏览器启动线程完成后的回调函数"""
        self.open_edge_btn.setEnabled(True)
        if success:
            self.status_label.setText(message)
            self.logger.info(f"浏览器启动成功: {message}")
        else:
            self.status_label.setText("启动失败")
            self.logger.error(f"浏览器启动失败: {message}")
            QMessageBox.critical(self, "错误", message)


def main():
    if Utils.is_already_running("LOCAL_PROXY_MUTEX"):
        return
    Utils.sync_work_dir()

    logger = LoggerManager()
    Utils.setup_except_hook(logger)
    Utils.qt_setup_high_dpi(logger)
    app = QApplication(sys.argv)

    # 设置应用字体，确保中文显示正常
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建并显示启动界面
    splash = SplashWindow()
    splash.show()
    app.processEvents()  # 立即更新界面显示

    # 初始化配置管理器，它会自动处理拉取/加载逻辑
    logger.info(f"========== 应用程序启动 (版本号{VERSION_CODE}) ==========")
    config_manager = ConfigManager(logger)

    # 关闭启动界面
    splash.close()

    # 检查是否是首次启动且配置拉取失败
    if config_manager.first_launch_config_failed:
        logger.error("首次启动配置拉取失败，本地无缓存配置")
        QMessageBox.critical(
            None,
            "严重错误",
            "首次启动失败！\n无法从管理员设备拉取配置，且本地无缓存配置。\n请检查网络连接或联系开发者获取配置文件。"
        )
        sys.exit(1)

    # 检查激活状态
    if not config_manager.is_activated():
        device_id = config_manager.get_disk_serial()
        check_result = config_manager.activation_check_result

        # 区分未激活和已过期
        if not check_result["device_activated"]:
            logger.error(f"软件未激活 - 设备ID: {device_id}")
            QMessageBox.critical(
                None,
                "软件未激活",
                f"软件未激活！\n请将本设备ID {device_id} 提供给开发者完成激活。"
            )
        else:
            logger.error(f"软件已过期 - 设备ID: {device_id}")
            QMessageBox.critical(
                None,
                "软件已过期",
                f"软件已过期！\n请将本设备ID {device_id} 提供给开发者续期。"
            )
        sys.exit(0)

    current_disk_serial = config_manager.get_disk_serial()
    password_status, has_password_set = config_manager.check_device_password(
        current_disk_serial)

    if not has_password_set:
        # 如果设备没有设置密码，直接进入
        logger.info(f"设备 {current_disk_serial} 未设置密码，直接进入")
        pass
    elif password_status:
        # 如果设置了密码且输入正确，进入
        logger.info(f"设备 {current_disk_serial} 密码验证成功，进入程序")
        pass
    else:
        # 如果设置了密码但输入错误或取消，退出
        logger.warning(f"设备 {current_disk_serial} 密码验证失败或用户取消，退出程序")
        sys.exit(0)

    # 获取当前程序的版本号和配置文件中定义的更新信息
    current_version = VERSION_CODE
    version_info = config_manager.data.get("version", {})
    force_update = version_info.get("force_update", True)
    update_content = version_info.get("update_content", "")
    latest_version = version_info.get("latest_vercode", 0)
    update_url = version_info.get("update_url", "")
    website_pwd = version_info.get("website_pwd", "")
    auto_update = version_info.get("auto_update", True)  # 添加自动更新配置
    zip_url = version_info.get("zip_url", "")
    zip_pwd = version_info.get("zip_pwd", "")
    extract_path = version_info.get("extract_path", "")

    logger.info(
        f"版本检查 - 当前版本: {current_version}, 最新版本: {latest_version}, 强制更新: {force_update}, 自动更新: {auto_update}")

    if current_version < latest_version:
        # 当前版本不是最新，检查是否启用自动更新
        if auto_update:
            # 启用自动更新，启动更新器
            logger.info("检测到新版本且启用了自动更新，启动更新器")
            
            # 构建更新器启动参数
            updater_args = [
                os.path.join(Utils.get_program_dir(), "Updater.exe"),
                f"--zip_url={zip_url}",
                f"--zip_pwd={zip_pwd}",
                f"--extract_path={extract_path}"
            ]
            
            try:
                # 启动更新器
                subprocess.Popen(updater_args)
                logger.info("更新器已启动，主程序退出")
                sys.exit(0)
            except Exception as e:
                logger.error(f"启动更新器失败: {e}")
        else:
            logger.info("检测到新版本但未启用自动更新，执行原有弹窗提醒")
            
            # 构建更新信息文本
            update_message = (
                f"检测到新版本！\n\n"
                f"最新版本号: {latest_version}\n"
                f"您的版本号: {current_version}\n\n"
            )

            # 如果有更新内容，添加到消息中
            if update_content:
                update_message += f"更新内容:\n{update_content}\n\n"

            # 根据是否强制更新显示不同提示
            if force_update:
                update_message += "本次更新为强制更新，请务必更新到最新版本。"
            else:
                update_message += "本次更新为可选更新，您可以忽略本次更新继续使用当前版本。"

            # 有网站密码
            if website_pwd:
                update_message += f"\n\n网站密码：{website_pwd}。"

            # 创建自定义对话框
            update_dialog = QMessageBox()
            update_dialog.setWindowTitle("版本更新提示")
            update_dialog.setIcon(QMessageBox.Warning)
            update_dialog.setText(update_message)

            # 创建按钮
            goto_button = None
            ignore_button = None
            exit_button = QPushButton("退出程序")

            # 如果存在更新地址，添加"去更新"按钮
            if update_url:
                goto_button = QPushButton("去更新")
                update_dialog.addButton(goto_button, QMessageBox.ActionRole)
            # 非强制更新：有忽略按钮
            if not force_update:
                ignore_button = QPushButton("忽略更新")
                update_dialog.addButton(ignore_button, QMessageBox.ActionRole)
            # 退出按钮
            update_dialog.addButton(exit_button, QMessageBox.RejectRole)

            # 连接按钮点击信号
            if goto_button:
                goto_button.clicked.connect(
                    lambda: update_dialog.done(0))  # 返回0表示去更新
            if ignore_button:
                ignore_button.clicked.connect(
                    lambda: update_dialog.done(1))  # 返回1表示忽略
            exit_button.clicked.connect(lambda: update_dialog.done(2))  # 返回2表示退出

            # 显示对话框并等待用户响应
            user_response = update_dialog.exec_()

            # 处理用户响应
            if user_response == 0:  # 用户点击了"去更新"
                webbrowser.open(update_url)
                logger.info(f"已通过默认浏览器打开更新地址: {update_url}，程序退出")
                sys.exit(0)
            elif user_response == 1:  # 用户点击了"忽略更新"
                logger.info("用户选择忽略更新，继续运行程序")
            elif user_response == 2:  # 用户点击了"退出程序"
                logger.info("用户选择退出程序")
                sys.exit(0)

    # 创建并显示主窗口
    window = MainWindow(logger, config_manager)
    window.show()
    logger.info("主窗口已显示，应用程序正常运行")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
