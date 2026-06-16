import ssl
import socks
import socket
import requests

from time import time
from urllib.parse import urlparse
from utils.UtilsLibs import LoggerManager
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor


class ServerScanner(QThread):
    """
    用于多线程扫描代理服务器的后台线程
    """
    scan_finished = pyqtSignal(list)
    update_status = pyqtSignal(str)

    def __init__(self, logger: LoggerManager, proxy_list, test_url):
        super().__init__()
        self.logger = logger

        self.proxy_list = self._parse_proxy_list(proxy_list)
        self.test_url = test_url
        self._parse_test_url()
        self.logger.debug(
            f"初始化服务器扫描线程 - 待扫描服务器数量: {len(proxy_list)}, 测试URL: {test_url}")

    def _parse_proxy_list(self, proxy_list):
        """解析代理服务器列表"""
        parsed_list = []

        for proxy in proxy_list:
            if isinstance(proxy, str):
                # 处理字符串格式: "socks5://172.16.194.243:1080" 或 "http://172.16.194.243:8080"
                try:
                    if proxy.startswith(('socks5://', 'http://')):
                        # 去除协议前缀
                        url_part = proxy.split('://')[1]
                        # 分割主机和端口
                        if ':' in url_part:
                            host, port_str = url_part.split(':', 1)
                            port = int(port_str)
                        else:
                            host = url_part
                            # 默认端口
                            port = 1080 if proxy.startswith(
                                'socks5://') else 8080

                        # 确定协议类型
                        protocol = 'socks5' if proxy.startswith(
                            'socks5://') else 'http'

                        parsed_list.append({
                            'ip': host,
                            'port': port,
                            'protocol': protocol
                        })
                    else:
                        self.logger.warning(f"跳过不支持的代理格式: {proxy}")
                except Exception as e:
                    self.logger.warning(f"解析代理字符串失败 {proxy}: {repr(e)}")
            else:
                self.logger.warning(f"跳过不支持的数据类型: {proxy}")

        return parsed_list

    def _parse_test_url(self):
        """解析测试URL，提取主机、端口、路径"""
        parsed = urlparse(self.test_url)
        self.test_host = parsed.hostname
        self.test_port = parsed.port or (
            443 if parsed.scheme == 'https' else 80)
        self.test_path = parsed.path or '/'
        self.test_scheme = parsed.scheme
        self.use_ssl = self.test_scheme == 'https'

        self.logger.debug(f"解析测试URL - 主机: {self.test_host}, 端口: {self.test_port}, "
                          f"路径: {self.test_path}, SSL: {self.use_ssl}")

    def check_proxy(self, proxy_info):
        """检查代理服务器是否可用"""
        ip = proxy_info["ip"]
        port = proxy_info["port"]
        protocol = proxy_info["protocol"]

        start_time = time()

        if protocol == "socks5":
            return self._check_socks5_proxy(ip, port, start_time)
        else:  # http
            return self._check_http_proxy(ip, port, start_time)

    def check_response_status(self, response_bytes):
        """检查HTTP响应状态码，返回True表示响应有效"""
        try:
            response_str = response_bytes.decode('utf-8', errors='ignore')
            first_line = response_str.split(
                '\r\n')[0] if response_str else ''

            if 'HTTP/' in first_line:
                parts = first_line.split(' ')
                if len(parts) >= 2:
                    status_code = parts[1]
                    # 接受 2xx 和 3xx 状态码
                    if status_code.startswith(('2', '3')):
                        return True
        except Exception as e:
            self.logger.debug(f"解析响应失败: {repr(e)}")

        return False

    def _check_socks5_proxy(self, ip, port, start_time):
        """检查SOCKS5代理服务器是否可用"""
        sock = None
        try:
            # 创建SOCKS5 socket
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, ip, port)
            sock.settimeout(5)

            # 连接到测试服务器
            sock.connect((str(self.test_host), self.test_port))

            # 构建HTTP请求
            http_request = (
                f"GET {self.test_path} HTTP/1.1\r\n"
                f"Host: {self.test_host}\r\n"
                f"Connection: close\r\n"
                f"User-Agent: FuckHYGF/1.0\r\n"
                f"\r\n"
            ).encode('utf-8')

            # 如果是HTTPS，进行TLS握手
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                sock = ssl_context.wrap_socket(
                    sock, server_hostname=self.test_host)

            # 发送HTTP请求
            sock.send(http_request)

            # 接收响应
            response = b''
            sock.settimeout(3)
            receive_start = time()
            while time() - receive_start < 3:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
                    if b'\r\n\r\n' in response:
                        break
                except socket.timeout:
                    break

            # 检查响应
            if self.check_response_status(response):
                latency = round((time() - start_time) * 1000)
                self.logger.info(
                    f"SOCKS5代理服务器 {ip}:{port} 可用，响应时间: {latency}ms")
                return {"ip": ip, "port": port, "protocol": "socks5", "latency": latency}
            else:
                self.logger.debug(
                    f"SOCKS5代理服务器 {ip}:{port} 响应无效: {response[:100]}")

        except socks.ProxyConnectionError as e:
            self.logger.debug(f"SOCKS5代理服务器 {ip}:{port} 代理连接失败: {repr(e)}")
        except socks.SOCKS5Error as e:
            self.logger.debug(f"SOCKS5代理服务器 {ip}:{port} SOCKS5协议错误: {repr(e)}")
        except socket.timeout:
            self.logger.debug(f"SOCKS5代理服务器 {ip}:{port} 连接超时")
        except ConnectionRefusedError:
            self.logger.debug(f"SOCKS5代理服务器 {ip}:{port} 连接被拒绝")
        except Exception as e:
            self.logger.debug(f"SOCKS5代理服务器 {ip}:{port} 检查失败: {repr(e)}")
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

        return None

    def _check_http_proxy(self, ip, port, start_time):
        """检查HTTP代理服务器是否可用"""
        try:
            # 构建代理URL
            proxy_url = f"http://{ip}:{port}"
            self.logger.debug(f"检查HTTP代理服务器: {proxy_url}")

            # 发送测试请求
            response = requests.get(
                self.test_url,
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=5,
            )

            if response.status_code in [200, 204]:
                latency = round((time() - start_time) * 1000)
                self.logger.info(
                    f"HTTP代理服务器 {proxy_url} 可用，响应时间: {latency}ms")
                return {"ip": ip, "port": port, "protocol": "http", "latency": latency}
            else:
                self.logger.debug(
                    f"HTTP代理服务器 {proxy_url} 返回状态码: {response.status_code}")

        except requests.exceptions.ConnectTimeout:
            self.logger.debug(f"HTTP代理服务器 {ip}:{port} 连接超时")
        except requests.exceptions.ConnectionError:
            self.logger.debug(f"HTTP代理服务器 {ip}:{port} 连接被拒绝")
        except requests.exceptions.ReadTimeout:
            self.logger.debug(f"HTTP代理服务器 {ip}:{port} 读取超时")
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"HTTP代理服务器 {ip}:{port} 检查失败: {repr(e)}")

        return None

    def run(self):
        results = []
        total_servers = len(self.proxy_list)

        self.update_status.emit(f"开始扫描 {total_servers} 个服务器...")
        self.logger.info(f"开始扫描 {total_servers} 个代理服务器")

        # 使用线程池并发扫描
        with ThreadPoolExecutor(max_workers=min(20, total_servers)) as executor:
            futures = [executor.submit(self.check_proxy, p)
                       for p in self.proxy_list]
            for i, future in enumerate(futures):
                result = future.result()
                if result:
                    results.append(result)

                progress = int(((i + 1) / total_servers) * 100)
                self.update_status.emit(
                    f"扫描进度: {progress}% ({i+1}/{total_servers})")

        results.sort(key=lambda x: x['latency'])
        self.logger.info(f"扫描完成，找到 {len(results)} 个可用代理服务器")
        self.update_status.emit(f"扫描完成。找到 {len(results)} 个可用服务器。")
        self.scan_finished.emit(results)
