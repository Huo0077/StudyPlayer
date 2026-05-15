import sys
import os
import subprocess
import threading
import urllib.request
import zipfile
import shutil
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer

# ============ VLC 自动安装向导 ============
class VLCSetupWizard(QMainWindow):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 StudyPlayer - 初始化")
        self.setFixedSize(500, 300)
        self.setStyleSheet("QMainWindow { background-color: #0a0a1a; } QLabel { color: #d1d1e0; } QPushButton { background-color: #6c63ff; color: white; border-radius: 8px; padding: 10px; font-weight: bold; } QProgressBar { background-color: #1a1a35; border: 1px solid #2a2a55; border-radius: 5px; text-align: center; color: white; } QProgressBar::chunk { background-color: #6c63ff; }")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.title = QLabel("正在准备播放环境")
        from PyQt5.QtGui import QFont
        self.title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        
        self.desc = QLabel("未检测到解码器。点击按钮自动配置本地环境。")
        self.desc.setWordWrap(True)
        self.desc.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        self.btn_start = QPushButton("立即下载并配置")
        self.btn_start.clicked.connect(self._start_install)
        
        layout.addWidget(self.title)
        layout.addWidget(self.desc)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_start)
        
        self.progress_signal.connect(self._update_ui)
        self.finished_signal.connect(self._on_finished)

    def _update_ui(self, val, status):
        self.progress_bar.setValue(val)
        self.title.setText(status)

    def _start_install(self):
        self.btn_start.hide()
        self.progress_bar.show()
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        try:
            url = "https://get.videolan.org/vlc/3.0.18/win64/vlc-3.0.18-win64.zip"
            zip_path = "vlc_temp.zip"
            def progress(count, block_size, total_size):
                p = int(count * block_size * 100 / (total_size or 1))
                self.progress_signal.emit(p, f"正在下载: {p}%")
            urllib.request.urlretrieve(url, zip_path, progress)
            
            self.progress_signal.emit(90, "正在解压...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall("vlc_extract")
            
            vlc_dir = os.path.join(os.getcwd(), "vlc_runtime")
            if os.path.exists(vlc_dir): shutil.rmtree(vlc_dir)
            inner = os.path.join("vlc_extract", os.listdir("vlc_extract")[0])
            shutil.move(inner, vlc_dir)
            os.remove(zip_path)
            shutil.rmtree("vlc_extract")
            self.finished_signal.emit()
        except Exception as e:
            self.progress_signal.emit(0, f"错误: {str(e)}")
            self.finished_signal.emit()

    def _on_finished(self):
        if self.progress_bar.value() >= 90:
            QMessageBox.information(self, "完成", "配置成功！请重启程序。")
            sys.exit(0)
        else:
            QMessageBox.critical(self, "失败", "配置失败。")
            self.btn_start.show()

def check_vlc():
    local_vlc = os.path.join(os.getcwd(), "vlc_runtime", "libvlc.dll")
    if os.path.exists(local_vlc):
        os.environ['PYTHON_VLC_MODULE_PATH'] = os.path.join(os.getcwd(), "vlc_runtime")
        return True
    try:
        import vlc
        if vlc.Instance(): return True
    except: pass
    return False

def run_app(app):
    from styles import DARK_THEME
    from player_window import PlayerWindow
    
    app.setStyleSheet(DARK_THEME)
    
    if not check_vlc():
        wizard = VLCSetupWizard()
        wizard.show()
        app.exec_()
        return

    window = PlayerWindow()
    
    # 全局鼠标监控，用于自动显示/隐藏控制栏
    class GlobalEventFilter(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.MouseMove:
                try:
                    # 确保窗口还在且可见
                    if window and not window.isMinimized() and window.isVisible():
                        # 获取鼠标相对于窗口的位置
                        pos = window.mapFromGlobal(event.globalPos())
                        if window.rect().contains(pos):
                            window._show_controls()
                except Exception:
                    pass
            return super().eventFilter(obj, event)
    
    event_filter = GlobalEventFilter()
    app.installEventFilter(event_filter)
    
    window.show()
    
    # 启动初始隐藏计时器
    window.hide_controls_timer.start()
    
    # 参数处理
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.exists(arg):
            window.playlist_widget.add_files([arg])
            window._play_file(arg)
            
    app.exec_()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    run_app(app)
