"""
自动更新器
负责下载并解压更新包
"""
import os
import time
import zipfile
import argparse
import tempfile
import threading
from urllib.parse import urlparse
import requests
from utils.UtilsLibs import Utils

# Tkinter GUI
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class AutoUpdater:
    def __init__(self, zip_url, zip_pwd, extract_path):
        self.zip_url = zip_url
        self.zip_pwd = zip_pwd.encode() if zip_pwd else None
        self.extract_path = os.path.expandvars(extract_path)
        
        # 解析URL中的文件名
        url_path = urlparse(zip_url).path
        self.zip_filename = os.path.basename(url_path)
        if not self.zip_filename:
            self.zip_filename = "update.zip"
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="update_")
        self.temp_zip_path = os.path.join(self.temp_dir, self.zip_filename)
        
        # 状态跟踪
        self.current_step = ""
        self.progress_value = 0
        self.is_downloading = False
        self.is_extracting = False
        self.error_message = ""
        
        # 创建GUI
        self.root = tk.Tk()
        self.root.title("自动更新")
        self.root.geometry("340x180")
        self.root.resizable(False, False)
        
        # 中心化窗口
        self.center_window()
        
        # 初始化UI
        self.init_ui()
        
        # 启动更新线程
        self.update_thread = threading.Thread(target=self.perform_update)
        self.update_thread.daemon = True
    
    def center_window(self):
        """将窗口移动到屏幕中央"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def init_ui(self):
        """初始化用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)) # type: ignore
        
        # 标题标签
        title_label = ttk.Label(
            main_frame, 
            text="正在更新中...", 
            font=("Microsoft YaHei", 12, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 步骤标签
        self.step_label = ttk.Label(
            main_frame,
            text="初始化...",
            font=("Microsoft YaHei", 9)
        )
        self.step_label.grid(row=1, column=0, pady=(0, 10))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            length=300
        )
        self.progress_bar.grid(row=2, column=0, pady=(0, 20))
        
        # 进度百分比标签
        self.percent_label = ttk.Label(
            main_frame,
            text="0%",
            font=("Microsoft YaHei", 9)
        )
        self.percent_label.grid(row=3, column=0)
    
    def update_step_label(self, text):
        """更新步骤标签"""
        self.current_step = text
        self.step_label.config(text=text)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_value = min(100, max(0, value))
        self.progress_bar['value'] = self.progress_value
        self.percent_label.config(text=f"{int(self.progress_value)}%")
        self.root.update_idletasks()
    
    def download_file(self):
        """下载压缩包文件"""
        self.is_downloading = True
        self.update_step_label("正在下载更新包...")
        
        try:
            response = requests.get(self.zip_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.temp_zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 50  # 下载占50%进度
                        self.update_progress(progress)
            
            self.update_progress(50)
            return True
            
        except Exception as e:
            self.error_message = f"下载失败: {str(e)}"
            return False
        finally:
            self.is_downloading = False
    
    def extract_file(self):
        """解压压缩包文件"""
        self.is_extracting = True
        self.update_step_label("正在解压文件...")
        
        try:
            if not os.path.exists(self.extract_path):
                os.makedirs(self.extract_path)
            
            with zipfile.ZipFile(self.temp_zip_path, 'r') as zip_ref:
                # 获取文件列表
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, filename in enumerate(file_list):
                    try:
                        zip_ref.extract(filename, self.extract_path, pwd=self.zip_pwd)
                    except:
                        try:
                            # 如果密码错误，尝试无密码解压
                            zip_ref.extract(filename, self.extract_path)
                        except Exception as e:
                            # 跳过更新器本身
                            exe_path = Utils.get_program_path()
                            exe_name = os.path.basename(exe_path).lower()
                            if filename.lower().endswith(exe_name):
                                pass
                            else:
                                self.error_message = f"解压文件失败: {str(e)}"
                                return False
                    
                    # 更新进度条 (解压占50%进度)
                    progress = 50 + ((i + 1) / total_files) * 50
                    self.update_progress(progress)
            
            self.update_progress(100)
            return True
            
        except zipfile.BadZipFile:
            self.error_message = "压缩包文件损坏"
            return False
        except Exception as e:
            self.error_message = f"解压失败: {str(e)}"
            return False
        finally:
            self.is_extracting = False
    
    def perform_update(self):
        """执行更新操作"""
        try:
            # 下载文件
            if not self.download_file():
                self.show_error()
                return
            
            # 解压文件
            if not self.extract_file():
                self.show_error()
                return
            
            # 更新完成
            self.update_step_label("更新完成！")
            time.sleep(2)
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass
            
            # 显示完成消息并退出
            self.root.after(0, self.show_success)
            
        except Exception as e:
            self.error_message = f"更新过程中发生错误: {str(e)}"
            self.show_error()
    
    def show_error(self):
        """显示错误信息"""
        messagebox.showerror("更新失败", self.error_message)
        self.root.after(0, self.root.quit)
    
    def show_success(self):
        """显示成功信息"""
        messagebox.showinfo("更新成功", "更新已完成！请重新启动程序。")
        self.root.after(0, self.root.quit)
    
    def run(self):
        """运行更新器"""
        # 启动更新线程
        self.update_thread.start()
        
        # 启动GUI事件循环
        self.root.mainloop()


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='自动更新器')
    parser.add_argument('--zip_url', type=str, required=True, help='压缩包下载链接')
    parser.add_argument('--zip_pwd', type=str, default='', help='压缩包密码')
    parser.add_argument('--extract_path', type=str, required=True, help='解压路径')
    
    # 解析参数
    try:
        args = parser.parse_args()
    except:
        # 如果命令行参数解析失败，显示帮助信息并退出
        parser.print_help()
        return
    
    # 运行更新器
    updater = AutoUpdater(args.zip_url, args.zip_pwd, args.extract_path)
    updater.run()


if __name__ == "__main__":
    main()