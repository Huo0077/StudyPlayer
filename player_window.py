"""主窗口"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QShortcut, QAction, QMenuBar, QSplitter,
    QApplication, QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QEvent
from PyQt5.QtGui import QKeySequence, QFont

from video_widget import VideoWidget
from controls_widget import ControlsWidget
from playlist_widget import PlaylistWidget
from segments_widget import SegmentsWidget
from note_canvas import NoteCanvas
from utils import get_filename, is_video_file, get_video_files_from_dir, format_time
import json


class PlayerWindow(QMainWindow):
    """视频播放器主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 StudyPlayer")
        self.setMinimumSize(900, 560)
        self.resize(1200, 720)

        self._is_fullscreen = False
        self._playlist_visible = True
        self._segments_visible = False
        self._current_video_metadata = {} # 存储当前视频的分段信息
        self._current_playing_file = None # 记录当前真正播放的文件路径

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._connect_signals()

        # 自动隐藏控制栏逻辑
        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)
        self.hide_controls_timer = QTimer(self)
        self.hide_controls_timer.setInterval(3000) # 3秒
        self.hide_controls_timer.timeout.connect(self._hide_controls)
        
        # 键盘加速计时器
        self.fast_forward_timer = QTimer(self)
        self.fast_forward_timer.setSingleShot(True)
        self.fast_forward_timer.timeout.connect(self._start_3x_speed)
        self._pre_fast_speed = 1.0
        self._is_fast_forwarding = False
        
        # 延迟初始化 VLC（需要在 show 之后）
        QTimer.singleShot(100, self._init_vlc)

    def _setup_ui(self):
        """构建 UI 布局"""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 上半部分：视频 + 播放列表
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 视频区域
        self.video_container = QWidget()
        self.video_container_layout = QVBoxLayout(self.video_container)
        self.video_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = VideoWidget()
        self.video_container_layout.addWidget(self.video_widget)

        # 笔记画布 (覆盖在视频上)
        self.note_canvas = NoteCanvas() # 顶级悬浮窗，独立于布局以覆盖原生视频层
        self.note_canvas.mouse_move_callback = self._on_mouse_moved_on_canvas
        # 初始大小会在 resizeEvent 中处理，或者在这里给个初始大小
        
        # 播放列表
        self.playlist_widget = PlaylistWidget()
        self.playlist_widget.btn_close.clicked.connect(self.toggle_playlist)
        self.playlist_widget.btn_add.clicked.connect(self.open_file)
        self.playlist_widget.setFocusPolicy(Qt.NoFocus)

        # 分段列表
        self.segments_widget = SegmentsWidget()
        self.segments_widget.setFocusPolicy(Qt.NoFocus)
        self.segments_widget.hide() # 初始隐藏

        content_layout.addWidget(self.video_container, 1)
        content_layout.addWidget(self.playlist_widget)
        content_layout.addWidget(self.segments_widget)

        self.content_widget = content_widget

        # 控制栏
        self.controls = ControlsWidget()

        main_layout.addWidget(content_widget, 1)
        main_layout.addWidget(self.controls)

        # 允许窗口拖拽文件
        self.setAcceptDrops(True)

    def _setup_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        open_file_action = QAction("打开文件(&O)...", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.open_file)

        open_folder_action = QAction("打开文件夹(&D)...", self)
        open_folder_action.setShortcut("Ctrl+D")
        open_folder_action.triggered.connect(self.open_folder)

        load_subtitle_action = QAction("加载外部字幕...", self)
        load_subtitle_action.triggered.connect(self._load_subtitle)

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_file_action)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # 播放菜单
        play_menu = menubar.addMenu("播放(&P)")

        play_pause_action = QAction("播放/暂停", self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self._toggle_play_pause)

        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self._stop)

        forward_action = QAction("快进 10 秒", self)
        forward_action.setShortcut("Right")
        forward_action.triggered.connect(self._forward)

        backward_action = QAction("后退 10 秒", self)
        backward_action.setShortcut("Left")
        backward_action.triggered.connect(self._backward)

        next_action = QAction("下一个(&N)", self)
        next_action.setShortcut("Ctrl+Right")
        next_action.triggered.connect(self._play_next)

        prev_action = QAction("上一个(&P)", self)
        prev_action.setShortcut("Ctrl+Left")
        prev_action.triggered.connect(self._play_prev)

        play_menu.addAction(play_pause_action)
        play_menu.addAction(stop_action)
        play_menu.addSeparator()
        play_menu.addAction(forward_action)
        play_menu.addAction(backward_action)
        play_menu.addSeparator()
        play_menu.addAction(next_action)
        play_menu.addAction(prev_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(lambda: QTimer.singleShot(0, self.toggle_fullscreen))

        playlist_action = QAction("播放列表(&L)", self)
        playlist_action.setShortcut("Ctrl+L")
        playlist_action.triggered.connect(self.toggle_playlist)

        snapshot_action = QAction("截屏(&S)", self)
        snapshot_action.setShortcut("S")
        snapshot_action.triggered.connect(self._take_snapshot)

        view_menu.addAction(fullscreen_action)
        view_menu.addAction(playlist_action)
        view_menu.addAction(snapshot_action)

    def _setup_shortcuts(self):
        """额外的快捷键"""
        # 音量
        QShortcut(QKeySequence(Qt.Key_Up), self, self._volume_up)
        QShortcut(QKeySequence(Qt.Key_Down), self, self._volume_down)
        # ---- 快捷键 (移至 keyPressEvent 处理，以便支持长按) ----
        # 空格, 左右键等在 keyPressEvent 中处理
        QShortcut(QKeySequence("Ctrl+Z"), self, self.note_canvas.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.note_canvas.redo)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_metadata)

    def _connect_signals(self):
        """连接信号 - V5 增强版"""
        # 1. 视频组件信号
        self.video_widget.openFileRequested.connect(self.open_file)
        self.video_widget.positionChanged.connect(self.controls.update_position)
        self.video_widget.durationChanged.connect(self.controls.update_duration)
        self.video_widget.playbackStateChanged.connect(self.controls.set_playing_state)
        self.video_widget.mediaEnded.connect(self._on_media_ended)
        self.video_widget.fileDropped.connect(self._handle_file_drop)
        
        # 使用 QTimer.singleShot 延迟触发全屏，防止在事件处理（如双击）期间同步改变窗口状态导致底层崩溃
        self.video_widget.doubleClicked.connect(lambda: QTimer.singleShot(0, self.toggle_fullscreen))

        # 2. 核心播放控制
        self.controls.playPauseClicked.connect(self._toggle_play_pause)
        self.controls.stopClicked.connect(self._stop)
        self.controls.prevClicked.connect(self._play_prev)
        self.controls.nextClicked.connect(self._play_next)
        self.controls.seekRequested.connect(self._seek)
        self.controls.volumeChanged.connect(self._set_volume)
        self.controls.muteClicked.connect(self._toggle_mute)
        self.controls.rateChanged.connect(self._set_rate)
        self.controls.snapshotClicked.connect(self._take_snapshot)

        # 3. 侧边栏/全屏切换
        self.controls.btn_playlist.clicked.connect(self.toggle_playlist)
        self.controls.btn_fullscreen.clicked.connect(lambda: QTimer.singleShot(0, self.toggle_fullscreen))
        self.controls.btn_settings.clicked.connect(self._show_settings_menu)
        self.controls.segmentsToggleClicked.connect(self.toggle_segments)
        
        # 4. 笔记/标记信号
        self.controls.notesToggleClicked.connect(self._toggle_notes)
        self.controls.colorSelected.connect(self.note_canvas.set_color)
        self.controls.toolSelected.connect(self.note_canvas.set_tool)
        self.controls.penWidthChanged.connect(self.note_canvas.set_pen_width)
        self.controls.newPageClicked.connect(self._note_new_page)
        self.controls.prevPageClicked.connect(self._note_prev_page)
        self.controls.nextPageClicked.connect(self._note_next_page)
        self.controls.undoClicked.connect(self.note_canvas.undo)
        self.controls.redoClicked.connect(self.note_canvas.redo)
        self.controls.clearNotesClicked.connect(self.note_canvas.clear_canvas)
        self.controls.aggregateNotesClicked.connect(self._show_aggregated_notes)
        
        # 5. 播放列表/分段信号
        self.playlist_widget.fileSelected.connect(self._play_file)
        self.segments_widget.addSegmentRequested.connect(self._save_new_segment)
        self.segments_widget.segmentSelected.connect(self._play_segment)
        self.segments_widget.segmentsChanged.connect(self._on_segments_changed)

    def _note_new_page(self):
        self.note_canvas.new_page()
        self._update_note_page_label()

    def _note_prev_page(self):
        if self.note_canvas.prev_page():
            self._update_note_page_label()

    def _note_next_page(self):
        if self.note_canvas.next_page():
            self._update_note_page_label()

    def _update_note_page_label(self):
        curr, total = self.note_canvas.get_page_info()
        self.controls.label_page.setText(f"{curr}/{total}")

    def _init_vlc(self):
        """初始化 VLC 渲染"""
        self.video_widget.setup_player()
        # 设置默认音量
        self.video_widget.set_volume(self.controls.volume_slider.value())

    # ============ 文件操作 ============

    def open_file(self):
        """打开文件对话框"""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.3gp *.ts *.rmvb);;所有文件 (*)"
        )
        if filepaths:
            self.playlist_widget.add_files(filepaths)
            # 如果当前没有播放，自动播放第一个
            if not self.video_widget.is_playing():
                self._play_file(filepaths[0])

    def open_folder(self):
        """打开文件夹"""
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if directory:
            video_files = get_video_files_from_dir(directory)
            if video_files:
                self.playlist_widget.add_files(video_files)
                if not self.video_widget.is_playing():
                    self._play_file(video_files[0])

    def _handle_file_drop(self, filepath):
        """处理文件拖拽"""
        self.playlist_widget.add_files([filepath])
        self._play_file(filepath)

    # ============ 播放控制 ============

    def _play_file(self, filepath):
        """播放指定文件"""
        # 保存旧文件的元数据
        self._save_metadata()
        
        # 更新当前真正播放的文件记录
        self._current_playing_file = filepath
        
        self.video_widget.load_media(filepath)
        self.video_widget.play()
        self.playlist_widget.highlight_file(filepath)
        self.setWindowTitle(f"🎬 {get_filename(filepath)}")
        self.controls.reset()
        
        # 加载新文件的元数据
        self._load_metadata(filepath)
        
        # 恢复当前倍速设置
        rate_text = self.controls.speed_combo.currentText()
        try:
            rate = float(rate_text.replace('x', ''))
        except ValueError:
            rate = 1.0
            
        # 延迟设置倍速和音量（等待媒体加载并开始播放）
        def delayed_setup():
            self.video_widget.set_rate(rate)
            # 再次强制设置音量，防止部分情况下初始化音量无效
            self.video_widget.set_volume(self.controls.volume_slider.value())
            
        QTimer.singleShot(500, delayed_setup)

    def _toggle_play_pause(self):
        """切换播放/暂停"""
        self.video_widget.toggle_play_pause()

    def _stop(self):
        """停止播放"""
        self.video_widget.stop()
        self.controls.reset()
        self.setWindowTitle("🎬 StudyPlayer")

    def _forward(self):
        """快进 10 秒"""
        self.video_widget.seek_relative(10000)

    def _backward(self):
        """后退 10 秒"""
        self.video_widget.seek_relative(-10000)

    def _seek(self, position_ms):
        """跳转到指定位置"""
        self.video_widget.seek(position_ms)

    def _set_volume(self, volume):
        """设置音量"""
        self.video_widget.set_volume(volume)

    def _volume_up(self):
        """增加音量"""
        vol = min(100, self.controls.volume_slider.value() + 5)
        self.controls.volume_slider.setValue(vol)

    def _volume_down(self):
        """减少音量"""
        vol = max(0, self.controls.volume_slider.value() - 5)
        self.controls.volume_slider.setValue(vol)

    def _toggle_mute(self):
        """切换静音"""
        self.video_widget.toggle_mute()
        is_muted = self.video_widget.is_muted()
        self.controls.set_mute_icon(is_muted)

    def _set_rate(self, rate):
        """设置播放速率"""
        self.video_widget.set_rate(rate)

    def _on_media_ended(self):
        """媒体播放结束"""
        # 自动播放下一个
        next_file = self.playlist_widget.get_next_file()
        if next_file:
            self._play_file(next_file)

    def _play_next(self):
        """播放下一个"""
        next_file = self.playlist_widget.get_next_file()
        if next_file:
            self._play_file(next_file)

    def _play_prev(self):
        """播放上一个"""
        prev_file = self.playlist_widget.get_prev_file()
        if prev_file:
            self._play_file(prev_file)

    # ============ 视图控制 ============

    def toggle_fullscreen(self):
        """切换全屏"""
        if self._is_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self):
        """进入全屏"""
        self._is_fullscreen = True
        self.showFullScreen()

    def _exit_fullscreen(self):
        """退出全屏"""
        if not self._is_fullscreen:
            return
        self._is_fullscreen = False
        self.showNormal()

    def toggle_playlist(self):
        """切换播放列表显示"""
        self._playlist_visible = not self._playlist_visible
        self.playlist_widget.setVisible(self._playlist_visible)

    def _show_settings_menu(self):
        """显示设置与信息菜单"""
        menu = QMenu(self)
        
        # 视频信息
        info_action = QAction("视频信息...", self)
        info_action.triggered.connect(self._show_media_info)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        # 宽高比子菜单
        aspect_menu = menu.addMenu("宽高比")
        ratios = [("默认", None), ("16:9", "16:9"), ("4:3", "4:3"), ("2.35:1", "2.35:1"), ("1:1", "1:1")]
        for label, ratio in ratios:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, r=ratio: self.video_widget.set_aspect_ratio(r))
            aspect_menu.addAction(action)
        
        # 字幕轨道子菜单
        sub_menu = menu.addMenu("字幕轨道")
        if hasattr(self.video_widget, 'get_subtitle_tracks'):
            tracks = self.video_widget.get_subtitle_tracks()
            if not tracks:
                sub_menu.addAction("无可用轨道").setEnabled(False)
            else:
                for tid, name in tracks:
                    action = QAction(name, self)
                    action.triggered.connect(lambda checked, i=tid: self.video_widget.set_subtitle_track(i))
                    sub_menu.addAction(action)
        else:
            sub_menu.addAction("组件版本不支持字幕管理").setEnabled(False)
            
        menu.exec_(self.controls.btn_settings.mapToGlobal(self.controls.btn_settings.rect().bottomLeft()))

    def _show_media_info(self):
        """弹出媒体详细信息"""
        info = self.video_widget.get_media_info()
        QMessageBox.information(self, "视频信息", info)

    def _load_subtitle(self):
        """加载外部字幕"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "字幕文件 (*.srt *.ass *.sub *.vtt);;所有文件 (*)"
        )
        if filepath:
            self.video_widget.set_subtitle_file(filepath)

    def _take_snapshot(self):
        """截屏"""
        success, path = self.video_widget.take_snapshot()
        if success:
            # 状态栏提示（如果需要可以加）
            QMessageBox.information(self, "截图成功", f"截图已保存至:\n{path}")
        else:
            QMessageBox.warning(self, "截图失败", "无法进行截图，请确保视频正在播放。")

    def toggle_segments(self):
        """切换分段面板显示"""
        self._segments_visible = not self._segments_visible
        if self._segments_visible:
            self._playlist_visible = False
            self.playlist_widget.hide()
            self.segments_widget.show()
            # 开启双滑块模式
            duration = self.video_widget.get_duration()
            if duration > 0:
                self.controls.progress_slider.setRange(0, duration)
                self.controls.progress_slider.set_range_mode(True)
                self.controls.progress_slider.set_range_values(0, duration)
        else:
            self.segments_widget.hide()
            self.controls.progress_slider.set_range_mode(False)

    def _save_new_segment(self, name):
        """保存当前滑块范围为新分段"""
        start = self.controls.progress_slider.start_pos
        end = self.controls.progress_slider.end_pos
        segments = self.segments_widget.add_segment(name, start, end)
        self._current_video_metadata["segments"] = segments
        self._save_metadata()

    def _play_segment(self, start, end):
        """跳转并播放分段"""
        self.video_widget.seek(start)
        self.video_widget.play()
        # 这里可以扩展：自动在 end 处停止或循环

    def _on_segments_changed(self, segments):
        """处理分段列表变化（如删除）"""
        self._current_video_metadata["segments"] = segments
        self._save_metadata()

    def _get_metadata_path(self, filepath):
        """获取元数据保存路径"""
        if not filepath:
            return None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        meta_dir = os.path.join(base_dir, "metadata")
        if not os.path.exists(meta_dir):
            os.makedirs(meta_dir)
        
        # 使用文件名的 hash 避免路径特殊字符问题
        import hashlib
        name_hash = hashlib.md5(filepath.encode('utf-8')).hexdigest()
        return os.path.join(meta_dir, f"{name_hash}.json")

    def _save_metadata(self):
        """保存分段数据到文件"""
        try:
            current_file = getattr(self, "_current_playing_file", None)
            if not current_file:
                return
                
            # 保存笔记数据
            if hasattr(self, 'note_canvas'):
                self._current_video_metadata["notes"] = self.note_canvas.get_notes_data()
                
            # 保存播放进度
            current_pos = self.video_widget.get_position()
            duration = self.video_widget.get_duration()
            
            # 判断是否接近播完 (剩余不足 30s)
            if duration > 0 and (duration - current_pos) < 30000:
                current_pos = 0 # 视为播完，重置进度
                
            if current_pos >= 0:
                 self._current_video_metadata["last_position"] = current_pos
            
            # 1. 保存为 JSON (详细元数据)
            path = self._get_metadata_path(current_file)
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self._current_video_metadata, f, ensure_ascii=False, indent=2)
            
            # 2. 保存到全局 progress.txt (简单历史记录)
            self._update_history_txt(current_file, current_pos)
            
        except Exception as e:
            print(f"保存元数据失败: {e}")

    def _update_history_txt(self, filepath, position):
        """更新专门的进度 TXT 文件 (如果 position 为 0 则删除记录)"""
        try:
            history_path = os.path.join(os.getcwd(), "progress.txt")
            history = {}
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '|' in line:
                            path, pos = line.strip().rsplit('|', 1)
                            history[path] = pos
            
            if position > 0:
                history[filepath] = str(position)
            elif filepath in history:
                del history[filepath]
            
            with open(history_path, 'w', encoding='utf-8') as f:
                for path, pos in history.items():
                    f.write(f"{path}|{pos}\n")
        except Exception as e:
            print(f"更新 progress.txt 失败: {e}")

    def _load_metadata(self, filepath):
        """从文件加载分段数据"""
        # 强制重置当前元数据，防止上一个视频的数据残留
        self._current_video_metadata = {"segments": [], "notes": {}, "last_position": 0}
        
        if not filepath:
            return
            
        path = self._get_metadata_path(filepath)
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._current_video_metadata = json.load(f)
            except Exception as e:
                print(f"加载 JSON 元数据失败: {e}")
        
        # 优先从 progress.txt 读取进度 (用户期望的文本记录)
        history_path = os.path.join(os.getcwd(), "progress.txt")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '|' in line:
                            path_str, pos_str = line.strip().rsplit('|', 1)
                            if path_str == filepath:
                                self._current_video_metadata["last_position"] = int(pos_str)
                                break
            except Exception as e:
                print(f"从 progress.txt 读取进度失败: {e}")

        self.segments_widget.set_segments(self._current_video_metadata.get("segments", []))
        if hasattr(self, 'note_canvas'):
            self.note_canvas.load_notes_data(self._current_video_metadata.get("notes", {}))
            
        # 恢复进度 - 增强版
        self._resume_pos = self._current_video_metadata.get("last_position", 0)
        
        # 清理旧计时器，防止并发冲突导致 RuntimeError
        if hasattr(self, '_resume_timer') and self._resume_timer:
            try:
                self._resume_timer.stop()
                self._resume_timer.deleteLater()
            except:
                pass
            self._resume_timer = None

        if self._resume_pos > 0:
            self._resume_attempts = 0
            self._resume_timer = QTimer(self)
            self._resume_timer.setInterval(200)
            self._resume_timer.timeout.connect(self._do_resume_seek)
            self._resume_timer.start()

    def _do_resume_seek(self):
        """执行进度恢复跳转"""
        if not hasattr(self, '_resume_timer') or not self._resume_timer:
            return
            
        self._resume_attempts += 1
        # 如果视频时长已加载，或者尝试次数过多，则执行跳转并停止计时器
        if self.video_widget.get_duration() > 0 or self._resume_attempts > 20:
            try:
                self.video_widget.seek(self._resume_pos)
                self._resume_timer.stop()
                self._resume_timer.deleteLater()
                self._resume_timer = None
            except:
                pass

    # ============ 笔记功能 ============

    def _toggle_notes(self, enabled):
        """切换笔记画布显示"""
        if enabled:
            self._sync_note_canvas_geometry()
            self.note_canvas.show()
            self.note_canvas.raise_()
        else:
            self.note_canvas.hide()

    def _show_aggregated_notes(self):
        """显示并自动保存汇总笔记"""
        image = self.note_canvas.get_combined_image(self.video_widget.size())
        
        # 1. 自动保存到专用文件夹
        save_dir = os.path.join(os.getcwd(), "notes_aggregated")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        import time
        filename = f"notes_agg_{int(time.time())}.png"
        save_path = os.path.join(save_dir, filename)
        image.save(save_path)
        
        # 2. 弹窗显示预览
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea
        from PyQt5.QtGui import QPixmap
        
        dialog = QDialog(self)
        dialog.setWindowTitle("汇总笔记 (长图滚动)")
        dialog.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(dialog)
        
        # 使用滚动区域支持长图
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #050510; border: none;")
        
        content_label = QLabel()
        pixmap = QPixmap.fromImage(image)
        content_label.setPixmap(pixmap)
        content_label.setAlignment(Qt.AlignCenter)
        
        scroll.setWidget(content_label)
        layout.addWidget(scroll)
        
        info_label = QLabel(f"笔记已自动保存至: {save_path}")
        info_label.setStyleSheet("color: #6c63ff; padding: 5px;")
        layout.addWidget(info_label)
        
        dialog.exec_()

    # ============ 事件处理 ============

    def resizeEvent(self, event):
        """同步笔记画布大小"""
        super().resizeEvent(event)
        # 计算缩放比例 (以 1000px 宽度为基准)
        # factor = self.width() / 1000.0
        # if hasattr(self, 'controls'):
        #     try:
        #         self.controls.scale_ui(factor)
        #     except:
        #         pass
        
        if hasattr(self, 'note_canvas') and self.note_canvas.isVisible():
            self._sync_note_canvas_geometry()

    def changeEvent(self, event):
        """处理窗口状态改变 (最小化/还原)"""
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.note_canvas.hide()
            elif self.isVisible() and self.controls.btn_notes.isChecked():
                self.note_canvas.show()
                self._sync_note_canvas_geometry()
        super().changeEvent(event)

    def closeEvent(self, event):
        """关闭窗口时清理"""
        # 退出前保存当前进度
        self._save_metadata()
        
        if hasattr(self, 'note_canvas'):
            self.note_canvas.close()
        if hasattr(self, 'video_widget'):
            self.video_widget.release()
        super().closeEvent(event)

    def moveEvent(self, event):
        """主窗口移动时同步笔记画布"""
        super().moveEvent(event)
        if hasattr(self, 'note_canvas') and self.note_canvas.isVisible():
            self._sync_note_canvas_geometry()

    def _sync_note_canvas_geometry(self):
        """将笔记画布对齐到视频渲染区域的全局位置"""
        if not hasattr(self, 'note_canvas'): return
        # 获取视频组件的全局几何信息
        try:
            video_geo = self.video_widget.geometry()
            global_pos = self.video_widget.mapToGlobal(QPoint(0, 0))
            self.note_canvas.setGeometry(
                global_pos.x(), global_pos.y(),
                video_geo.width(), video_geo.height()
            )
        except:
            pass

    def _hide_controls(self):
        """隐藏控制栏 - 极致极简模式"""
        # 如果鼠标不在控制栏上，且不是在播放列表/分段列表上方，则隐藏
        if not self.controls.underMouse() and not self.playlist_widget.underMouse():
            self.controls.hide()
            if self._is_fullscreen:
                self.setCursor(Qt.BlankCursor) # 仅全屏时隐藏鼠标

    def _show_controls(self):
        """显示控制栏"""
        try:
            if not self.controls or self.controls.parent() is None: return
            
            if self.controls.isHidden():
                self.controls.show()
            
            if self.cursor().shape() != Qt.ArrowCursor:
                self.setCursor(Qt.ArrowCursor)
                
            self.hide_controls_timer.start() # 重置计时器
        except:
            pass

    def _on_mouse_moved_on_canvas(self):
        """处理来自笔记画布的鼠标移动，带频率限制"""
        import time
        curr = time.time()
        if not hasattr(self, '_last_move_time'): self._last_move_time = 0
        if curr - self._last_move_time > 0.1:
            self._show_controls()
            self._last_move_time = curr

    def mouseMoveEvent(self, event):
        """处理鼠标移动以显示控制栏"""
        super().mouseMoveEvent(event)
        self._show_controls()

    def keyPressEvent(self, event):
        """处理键盘快捷键"""
        key = event.key()
        if key == Qt.Key_Space:
            self._toggle_play_pause()
        elif key == Qt.Key_Left:
            self._backward()
        elif key == Qt.Key_Right:
            if not event.isAutoRepeat():
                self._forward() # 单击快进 10s
                self.fast_forward_timer.start(500) # 500ms 后开启 3倍速
        elif key == Qt.Key_F:
            QTimer.singleShot(0, self.toggle_fullscreen)
        elif key == Qt.Key_Escape:
            if self._is_fullscreen:
                QTimer.singleShot(0, self._exit_fullscreen)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """处理键盘释放"""
        key = event.key()
        if key == Qt.Key_Right:
            self.fast_forward_timer.stop()
            if self._is_fast_forwarding:
                self._stop_3x_speed()
        super().keyReleaseEvent(event)

    def _start_3x_speed(self):
        """进入三倍速"""
        self._is_fast_forwarding = True
        self._pre_fast_speed = self.video_widget.get_rate()
        self.video_widget.set_rate(3.0)
        self.controls.speed_combo.setCurrentText("3.0x")

    def _stop_3x_speed(self):
        """恢复原速"""
        self._is_fast_forwarding = False
        self.video_widget.set_rate(self._pre_fast_speed)
        self.controls.speed_combo.setCurrentText(f"{self._pre_fast_speed}x")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files_to_add = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path) and is_video_file(path):
                files_to_add.append(path)
            elif os.path.isdir(path):
                files_to_add.extend(get_video_files_from_dir(path))

        if files_to_add:
            self.playlist_widget.add_files(files_to_add)
            if not self.video_widget.is_playing():
                self._play_file(files_to_add[0])

