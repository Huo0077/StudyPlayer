"""VLC 视频渲染组件"""

import sys
import os

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from utils import format_time, is_video_file, get_app_root

# 优先检查本地运行时
local_vlc_path = os.path.join(get_app_root(), "vlc_runtime")
if os.path.exists(local_vlc_path):
    os.environ['PYTHON_VLC_MODULE_PATH'] = local_vlc_path

try:
    import vlc
    VLC_AVAILABLE = True
except (ImportError, OSError):
    VLC_AVAILABLE = False

class VideoWidget(QFrame):
    """基于 VLC 的视频渲染组件"""

    # 自定义信号 - 必须在类级别定义
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    playbackStateChanged = pyqtSignal(bool)
    mediaEnded = pyqtSignal()
    doubleClicked = pyqtSignal()
    openFileRequested = pyqtSignal()
    fileDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoFrame")
        self.setMinimumSize(480, 270)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.NoFocus)

        # 移除这三个属性防止 hint_container 发生残影（即重叠）
        # 实际 VLC 渲染是挂载在 render_frame 上的，VideoWidget 自身不需要这些。

        # 创建专门用于 VLC 渲染的底层 Frame
        self.render_frame = QFrame(self)
        self.render_frame.setStyleSheet("background-color: black;")
        self.render_frame.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.render_frame.setAttribute(Qt.WA_PaintOnScreen, True)
        self.render_frame.setAttribute(Qt.WA_NoSystemBackground, True)
        self.render_frame.setFocusPolicy(Qt.NoFocus)
        self.render_frame.hide()

        # 极致还原参考图的空状态 UI
        self._setup_hint_ui()

        # VLC 实例
        self._init_vlc()

        # 轮询定时器
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._poll_position)

        self._duration = 0
        self._current_media_path = None
        self._is_playing = False

    def _setup_hint_ui(self):
        self._layout = QVBoxLayout(self)
        self.hint_container = QWidget()
        hint_v_layout = QVBoxLayout(self.hint_container)
        hint_v_layout.setAlignment(Qt.AlignCenter)
        hint_v_layout.setSpacing(15)

        self.icon_label = QLabel("📄")
        self.icon_label.setStyleSheet("font-size: 80px; color: #6c63ff; margin-bottom: 10px;")
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.hint_label = QLabel("拖拽视频文件到此处")
        self.hint_label.setStyleSheet("font-size: 20px; color: #ffffff; font-weight: bold;")
        
        self.sub_hint_label = QLabel("或点击 “打开文件” 按钮选择文件")
        self.sub_hint_label.setStyleSheet("font-size: 14px; color: #8888a0;")

        self.btn_open_file = QPushButton("📁 打开文件")
        self.btn_open_file.setObjectName("openFileButton")
        self.btn_open_file.setFixedSize(160, 44)
        self.btn_open_file.setCursor(Qt.PointingHandCursor)
        self.btn_open_file.clicked.connect(self.openFileRequested.emit)

        hint_v_layout.addWidget(self.icon_label)
        hint_v_layout.addWidget(self.hint_label)
        hint_v_layout.addWidget(self.sub_hint_label)
        hint_v_layout.addWidget(self.btn_open_file, 0, Qt.AlignCenter)

        self._layout.addWidget(self.hint_container)

    def _init_vlc(self):
        if VLC_AVAILABLE:
            vlc_args = [
                '--no-video-title-show', 
                '--no-stats', 
                '--no-sub-autodetect-file',
                '--avcodec-hw=any',
                '--network-caching=1000',
                '--file-logging', '--logfile=vlc_log.txt', '--logmode=text',
                '--verbose=1' # 适度日志
            ]
            self.vlc_instance = vlc.Instance(vlc_args)
            self.vlc_instance.log_unset()
            self.media_player = self.vlc_instance.media_player_new()
        else:
            self.vlc_instance = None
            self.media_player = None

    def setup_player(self):
        if not self.media_player: return
        # 强制创建原生窗口句柄
        hwnd = int(self.render_frame.winId())
        if sys.platform == 'win32':
            self.media_player.set_hwnd(hwnd)
        elif sys.platform.startswith('linux'):
            self.media_player.set_xwindow(hwnd)
        elif sys.platform == 'darwin':
            self.media_player.set_nsobject(hwnd)

    def load_media(self, filepath):
        if not self.vlc_instance:
            print("错误: VLC 实例未初始化，无法加载媒体。")
            return
        self._current_media_path = filepath
        media = self.vlc_instance.media_new(filepath)
        self.media_player.set_media(media)
        self.hint_container.hide()
        self.render_frame.show()

    def play(self):
        if self._current_media_path is None: return
        self.media_player.play()
        self._timer.start()
        self._is_playing = True
        self.playbackStateChanged.emit(True)

    def pause(self):
        self.media_player.pause()
        self._is_playing = False
        self.playbackStateChanged.emit(False)

    def toggle_play_pause(self):
        if self._current_media_path is None: return
        if self.media_player.is_playing(): self.pause()
        else: self.play()

    def stop(self):
        self.media_player.stop()
        self._timer.stop()
        self._is_playing = False
        self._duration = 0
        self.playbackStateChanged.emit(False)
        self.positionChanged.emit(0)
        self.render_frame.hide()
        self.hint_container.show()

    def is_playing(self):
        return self.media_player.is_playing() if self.media_player else False

    def seek(self, position_ms):
        if self.media_player: self.media_player.set_time(position_ms)

    def seek_relative(self, delta_ms):
        if not self.media_player: return
        current = self.media_player.get_time()
        if current < 0: current = 0
        new_pos = max(0, min(current + delta_ms, self._duration))
        self.media_player.set_time(new_pos)

    def set_rate(self, rate):
        if self.media_player: self.media_player.set_rate(rate)

    def set_volume(self, volume):
        if self.media_player: self.media_player.audio_set_volume(volume)

    def toggle_mute(self):
        if self.media_player: self.media_player.audio_toggle_mute()

    def is_muted(self):
        if self.media_player:
            return self.media_player.audio_get_mute()
        return False

    def _poll_position(self):
        if not self.media_player: return
        state = self.media_player.get_state()
        if state == vlc.State.Ended:
            self._timer.stop()
            self._is_playing = False
            self.playbackStateChanged.emit(False)
            self.mediaEnded.emit()
            return
        duration = self.media_player.get_length()
        if duration > 0 and duration != self._duration:
            self._duration = duration
            self.durationChanged.emit(duration)
        position = self.media_player.get_time()
        if position >= 0: self.positionChanged.emit(position)
        
    def resizeEvent(self, event):
        """处理尺寸变化"""
        super().resizeEvent(event)
        # 同步渲染层的大小
        if hasattr(self, 'render_frame'):
            self.render_frame.setGeometry(0, 0, self.width(), self.height())

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if is_video_file(filepath):
                self.fileDropped.emit(filepath)
    def take_snapshot(self):
        """截取当前画面并保存"""
        if not self.media_player: return False
        
        # 创建截图目录
        save_dir = os.path.join(os.getcwd(), "snapshots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        import time
        filename = f"snapshot_{int(time.time())}.png"
        filepath = os.path.join(save_dir, filename)
        
        # VLC 截图接口 (视频输出序号, 路径, 宽, 高)
        # 宽、高设为 0 表示使用原始分辨率
        res = self.media_player.video_take_snapshot(0, filepath, 0, 0)
        return res == 0, filepath

    def set_aspect_ratio(self, ratio):
        if self.media_player:
            self.media_player.video_set_aspect_ratio(ratio.encode() if ratio else None)

    def get_subtitle_tracks(self):
        if not self.media_player: return []
        desc = self.media_player.video_get_spu_description()
        if not desc: return []
        tracks = []
        for track_id, track_name in desc:
            if track_id >= 0:
                name_str = track_name.decode('utf-8') if isinstance(track_name, bytes) else track_name
                tracks.append((track_id, name_str))
        return tracks

    def set_subtitle_track(self, track_id):
        if self.media_player:
            self.media_player.video_set_spu(track_id)

    def get_media_info(self):
        if not self.media_player:
            return "暂无视频信息"
        state = "播放中" if self.is_playing() else "已暂停或停止"
        info = f"播放状态: {state}\n时长: {format_time(self._duration)}\n当前进度: {format_time(self.media_player.get_time())}"
        return info

    def get_duration(self):
        return self._duration

    def get_position(self):
        if self.media_player:
            return self.media_player.get_time()
        return 0

    def get_rate(self):
        if self.media_player:
            return self.media_player.get_rate()
        return 1.0

    def release(self):
        self._timer.stop()
        if self.media_player:
            self.media_player.stop()
            self.media_player.release()
        if self.vlc_instance:
            self.vlc_instance.release()
