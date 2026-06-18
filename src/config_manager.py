import os
import wmi
import json
import requests

from datetime import datetime
from cryptography.fernet import Fernet
from utils.UtilsLibs import LoggerManager
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QLineEdit


# 管理员设备IP地址列表
ADMIN_IPS = [
    "172.16.192.1",  # 电视盒子
    "172.16.194.149",  # 13班备用 (管控状态)
    "172.16.194.91",  # 13班备用 (开网状态)
    "172.16.114.21",  # 15班
    "localhost"  # 本地开发
]
ADMIN_PORT = 80  # 管理员设备端口

# 程序版本号
VERSION_CODE = 202606171


class ConfigManager:
    """
    配置管理器，负责加载、保存和从管理员设备拉取配置。
    每次启动时都会尝试拉取最新配置，失败则使用本地缓存。
    """

    def __init__(self, logger: LoggerManager, config_file="config.json"):
        self.logger = logger
        self.config_file = config_file

        self.data = {}
        self.admin_ip = ""
        self.first_launch_config_failed = False

        self.load_config()

    def load_config(self):
        """
        加载配置。优先尝试从固定管理员设备拉取最新配置，
        如果拉取失败，则加载本地已存在的配置文件。
        """
        self.logger.info("正在尝试从管理员设备拉取最新配置...")
        pull_success = self.fetch_config_from_admin()

        if pull_success:
            self.logger.info("配置拉取成功，已更新本地文件。")
            # 成功拉取后，数据已在 self.data 中，无需再次加载
        else:
            self.logger.warning("配置拉取失败，尝试加载本地缓存...")
            local_config_exists = self._load_local_config()
            if not local_config_exists:
                # 如果本地也没有配置文件，给出错误提示并初始化空配置
                self.logger.error(f"本地配置文件 {self.config_file} 不存在")
                self.data = {}
                # 首次启动且配置拉取失败的标记
                self.first_launch_config_failed = True
            else:
                self.logger.info("已加载本地缓存的配置。")

    def fetch_config_from_admin(self):
        """
        从管理员设备拉取配置，支持多个IP地址。
        按顺序尝试，直到成功或全部失败。
        """
        # 按顺序尝试每个IP地址
        for admin_ip in ADMIN_IPS:
            admin_url = f"http://{admin_ip}:{ADMIN_PORT}/localproxy/get_config?ver={VERSION_CODE}"

            try:
                self.logger.info(f"正在尝试从管理员服务器拉取配置: {admin_url}")
                response = requests.get(admin_url, timeout=3)

                if response.status_code == 200:
                    self.data = response.json()
                    self.logger.debug(f"从 {admin_ip} 成功拉取配置数据")
                    self.save_config()
                    self.admin_ip = admin_ip
                    return True
                else:
                    self.logger.warning(
                        f"管理员服务器 {admin_ip} 返回错误状态码: {response.status_code}")

            except requests.RequestException as e:
                self.logger.warning(f"连接管理员设备 {admin_ip} 失败: {repr(e)}")

        # 所有IP都尝试失败
        self.logger.error("所有管理员IP地址尝试均失败")
        return False

    def _get_fernet_key(self):
        """生成或获取固定的加密密钥"""
        return b"6dkALWYuO_ai8zffravhQ0hn51YvVllYtEwAQyUGAp4="  # 必须是32字节长

    def _encrypt_data(self, data_str):
        """加密数据字符串"""
        f = Fernet(self._get_fernet_key())
        return f.encrypt(data_str.encode('utf-8'))

    def _decrypt_data(self, encrypted_bytes):
        """解密数据字节"""
        f = Fernet(self._get_fernet_key())
        return f.decrypt(encrypted_bytes).decode('utf-8')

    def _load_local_config(self):
        """加载本地配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:  # 以二进制模式读取
                    encrypted_data = f.read()
                decrypted_data_str = self._decrypt_data(encrypted_data)
                self.data = json.loads(decrypted_data_str)
                self.logger.debug("本地配置文件加载并解密成功")
                return True
            except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                self.logger.error(f"加载或解密本地配置文件失败: {repr(e)}", exc_info=True)
                return False
        return False

    def save_config(self):
        """将当前配置加密后保存到本地文件"""
        try:
            data_str = json.dumps(self.data, indent=4,
                                  ensure_ascii=False)  # 格式化原生JSON
            encrypted_data = self._encrypt_data(data_str)
            with open(self.config_file, "wb") as f:
                f.write(encrypted_data)
            self.logger.info("配置已加密并保存到本地JSON文件")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {repr(e)}", exc_info=True)

    def is_activated(self):
        """检查软件是否已激活。现在支持多设备激活"""
        current_disk_serial = self.get_disk_serial()
        current_time = datetime.now()
        self.logger.debug(
            f"激活检查 - 当前设备ID: {current_disk_serial}, 当前时间: {current_time}")

        # 获取已激活的磁盘序列号列表
        activated_devices_map = self.data.get(
            "activated_devices_passwords", {})
        activated_disk_serials = list(activated_devices_map.keys())
        self.logger.debug(f"已激活设备列表: {activated_disk_serials}")

        # 检查当前设备的序列号是否在激活列表中
        is_current_device_activated = current_disk_serial in activated_disk_serials
        self.logger.debug(f"设备是否在激活列表中: {is_current_device_activated}")

        # 自动上报未激活设备ID到服务端
        if not is_current_device_activated:
            try:
                # 尝试上报设备ID
                response = requests.post(
                    f"http://{self.admin_ip}:{ADMIN_PORT}/localproxy/post_activate",
                    json={"device_id": current_disk_serial},
                    timeout=3  # 设置超时时间
                )
                if response.status_code == 200:
                    self.logger.info(f"设备ID {current_disk_serial} 上报成功")
                else:
                    self.logger.warning(
                        f"设备ID上报失败，状态码: {response.status_code}")
            except requests.RequestException as e:
                self.logger.error(f"设备ID上报失败: {repr(e)}")

        # 检查软件是否过期
        try:
            expiry_str = self.data.get("expiry_date", "")
            if expiry_str:
                expiry_time = datetime.strptime(
                    expiry_str, "%Y-%m-%d %H:%M:%S")
                is_not_expired = current_time < expiry_time
                self.logger.debug(
                    f"过期时间: {expiry_time}, 是否未过期: {is_not_expired}")
            else:
                is_not_expired = False
                self.logger.warning("配置中未设置过期时间")
        except ValueError as e:
            is_not_expired = False
            self.logger.error(f"解析过期时间失败: {repr(e)}", exc_info=True)

        # 记录激活状态检查结果
        self.activation_check_result = {
            "device_activated": is_current_device_activated,
            "not_expired": is_not_expired,
            "device_id": current_disk_serial
        }

        # 只有当设备被激活且软件未过期时，才返回 True
        return is_current_device_activated and is_not_expired

    def check_device_password(self, disk_serial):
        """
        检查指定磁盘序列号的密码是否正确。
        :param disk_serial: 磁盘序列号
        :return: (密码输入状态, 是否有密码设置)
                 密码输入状态: True(正确), False(错误或取消), None(未设置)
                 是否有密码设置: True/False
        """
        activated_devices_map = self.data.get(
            "activated_devices_passwords", {})
        correct_password = activated_devices_map.get(disk_serial)
        has_password = correct_password is not None and correct_password != ""
        self.logger.debug(
            f"检查设备 {disk_serial} 密码 - 是否设置密码: {has_password}")

        if not has_password:
            # 此设备没有设置密码
            return None, False  # 返回 (未设置, 未设置标志)

        # 循环直到输入正确或取消
        while True:
            password, ok = QInputDialog.getText(
                None, '程序密码', f'请输入设备 "{disk_serial}" 的密码:', echo=QLineEdit.Password
            )
            if not ok:
                # 用户点击了取消，中断程序
                self.logger.info(f"用户取消输入设备 {disk_serial} 的密码")
                return False, True  # 返回 (失败, 已设置标志)

            if password == correct_password:
                self.logger.info(f"设备 {disk_serial} 密码验证成功")
                return True, True  # 返回 (成功, 已设置标志)
            else:
                # 输入错误，弹窗提示并重新循环
                self.logger.warning(f"设备 {disk_serial} 密码输入错误")
                QMessageBox.warning(None, "密码错误", "密码不正确，请重试。")
                continue

    def get_disk_serial(self):
        """获取当前设备的硬盘序列号 (Windows)"""
        try:
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                if disk.MediaType == "Fixed hard disk media":
                    serial = disk.SerialNumber.strip()
                    self.logger.debug(f"获取到硬盘序列号: {serial}")
                    return serial
            self.logger.warning("未找到固定硬盘，返回UNKNOWN")
            return "UNKNOWN"
        except Exception as e:
            self.logger.error(f"获取硬盘序列号失败: {repr(e)}", exc_info=True)
            return "UNKNOWN"
