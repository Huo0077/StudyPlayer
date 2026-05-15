"""
🚀 视频播放器一键安装程序 (Setup Wizard)
功能：
1. 自动检测并下载 VLC 运行时 (便携版)
2. 安装 Python 依赖
3. 完成环境配置并启动播放器
"""

import sys
import os
import subprocess
import threading
import urllib.request
import zipfile
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

# 颜色与样式
STYLE = """
QMainWindow {
    background-color: #0a0a1a;
}
QLabel {
    color: #d1d1e0;
}
QPushButton {
    background-color: #6c63ff;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #8b83ff;
}
QProgressBar {
    background-color: #1a1a35;
    border: 1px solid #2a2a55;
    border-radius: 5px;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #6c63ff;
}
"""

class SetupWizard(QMainWindow):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 StudyPlayer - 安装向导")
        self.setFixedSize(500, 350)
        self.setStyleSheet(STYLE)
        
        self._setup_ui()
        self.progress_signal.connect(self._update_progress)
        self.finished_signal.connect(self._on_finished)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        self.title = QLabel("欢迎使用视频播放器")
        self.title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)

        self.desc = QLabel("本向导将为您准备播放环境，包括安装必要的组件和解码器。")
        self.desc.setWordWrap(True)
        self.desc.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #a1a1aa;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.btn_start = QPushButton("立即开始安装")
        self.btn_start.clicked.connect(self._start_install)

        layout.addWidget(self.title)
        layout.addWidget(self.desc)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_start)

    def _start_install(self):
        self.btn_start.setEnabled(False)
        self.progress_bar.show()
        self.desc.setText("正在配置环境，请稍候...")
        
        # 开启后台线程
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _update_progress(self, val, status):
        self.progress_bar.setValue(val)
        self.status_label.setText(status)

    def _install_thread(self):
        try:
            # 1. 检查并安装 Python 依赖
            self.progress_signal.emit(10, "正在安装 Python 依赖库...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])

            # 2. 检查 VLC 环境
            self.progress_signal.emit(30, "正在检查 VLC 解码器...")
            
            vlc_dir = os.path.join(os.getcwd(), "vlc_runtime")
            if not os.path.exists(vlc_dir):
                self.progress_signal.emit(40, "正在从服务器获取解码组件 (约 80MB)...")
                # 下载便携版 VLC
                # 注意：这里使用一个稳定的下载链接，实际发布时可替换为自己的 CDN
                url = "https://get.videolan.org/vlc/3.0.18/win64/vlc-3.0.18-win64.zip"
                zip_path = "vlc_temp.zip"
                
                # 自定义下载回调以显示进度
                def download_progress(count, block_size, total_size):
                    percent = int(count * block_size * 100 / total_size)
                    self.progress_signal.emit(40 + int(percent * 0.4), f"正在下载解码器: {percent}%")

                urllib.request.urlretrieve(url, zip_path, download_progress)
                
                self.progress_signal.emit(85, "正在解压解码器...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("vlc_extract")
                
                # 移动到目标目录
                extracted_folder = os.path.join("vlc_extract", "vlc-3.0.18")
                if os.path.exists(extracted_folder):
                    shutil.move(extracted_folder, vlc_dir)
                
                # 清理临时文件
                os.remove(zip_path)
                shutil.rmtree("vlc_extract")

            self.progress_signal.emit(100, "安装完成！")
            self.finished_signal.emit()

        except Exception as e:
            self.progress_signal.emit(0, f"发生错误: {str(e)}")
            self.finished_signal.emit()

    def _on_finished(self):
        if self.progress_bar.value() == 100:
            QMessageBox.information(self, "安装成功", "播放器环境已配置完成！点击确定启动播放器。")
            # 启动主程序
            subprocess.Popen([sys.executable, "main.py"])
            self.close()
        else:
            QMessageBox.critical(self, "安装失败", f"安装过程中出现问题：\n{self.status_label.text()}")
            self.btn_start.setEnabled(True)

if __name__ == "__main__":
    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec_())
