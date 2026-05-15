import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QComboBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QTimer

def format_time(ms):
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

class CustomSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_range_mode = False
        self.start_pos = 0
        self.end_pos = 0

    def set_range_mode(self, enabled):
        self.is_range_mode = enabled

    def set_range_values(self, start, end):
        self.start_pos = start
        self.end_pos = end

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.is_range_mode:
            val = self.minimum() + (self.maximum() - self.minimum()) * event.x() / self.width()
            if event.button() == Qt.RightButton:
                self.end_pos = int(val)
            else:
                self.start_pos = int(val)

class ControlsWidget(QWidget):
    """极致拟态风格控制栏 - 支持动态缩放"""
    
    # 核心播放信号
    playPauseClicked = pyqtSignal()
    stopClicked = pyqtSignal()
    prevClicked = pyqtSignal()
    nextClicked = pyqtSignal()
    backwardClicked = pyqtSignal()
    forwardClicked = pyqtSignal()
    seekRequested = pyqtSignal(int)
    volumeChanged = pyqtSignal(int)
    muteClicked = pyqtSignal()
    rateChanged = pyqtSignal(float)
    playlistToggleClicked = pyqtSignal(bool)
    segmentsToggleClicked = pyqtSignal(bool)
    fullscreenToggleClicked = pyqtSignal()
    snapshotClicked = pyqtSignal()
    
    # 笔记/标记信号
    notesToggleClicked = pyqtSignal(bool)
    toolSelected = pyqtSignal(str)
    colorSelected = pyqtSignal(str)
    penWidthChanged = pyqtSignal(int)
    undoClicked = pyqtSignal()
    redoClicked = pyqtSignal()
    clearNotesClicked = pyqtSignal()
    aggregateNotesClicked = pyqtSignal()
    
    # 多页笔记信号
    newPageClicked = pyqtSignal()
    prevPageClicked = pyqtSignal()
    nextPageClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlsContainer")
        self._is_seeking = False
        self.setFocusPolicy(Qt.NoFocus)
        
        # 存储所有动态缩放的组件
        self._scalable_buttons = []
        self._scalable_labels = []
        self._scalable_layouts = []
        
        self._setup_ui()

    def _setup_ui(self):
        """核心 UI 布局逻辑"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 15, 20, 20)
        self.main_layout.setSpacing(15)
        self._scalable_layouts.append((self.main_layout, 20, 15))

        # 1. 进度条区域
        progress_layout = QHBoxLayout()
        self.label_time = QLabel("00:00")
        self.label_time.setObjectName("progressLabel")
        self.label_time.setStyleSheet("font-size: 11px; color: #8888a0;")
        self._scalable_labels.append((self.label_time, 11))
        
        self.progress_slider = CustomSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("progressSlider")
        self.progress_slider.setCursor(Qt.PointingHandCursor)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.setFocusPolicy(Qt.NoFocus)
        
        self.label_duration = QLabel("00:00")
        self.label_duration.setObjectName("progressLabel")
        self.label_duration.setStyleSheet("font-size: 11px; color: #8888a0;")
        self._scalable_labels.append((self.label_duration, 11))
        
        progress_layout.addWidget(self.label_time)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.label_duration)
        self.main_layout.addLayout(progress_layout)

        # 2. 底部控制组
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(25)
        self._scalable_layouts.append((self.bottom_layout, 0, 25))

        # --- 左侧组: 播放列表 & 标记开关 ---
        left_group = QHBoxLayout()
        left_group.setSpacing(15)
        self.btn_playlist_container = self._create_labeled_button("播放列表", "⋮≡", self.playlistToggleClicked, checkable=True)
        self.btn_notes_container = self._create_labeled_button("书签", "🔖", self._on_notes_toggled, checkable=True)
        self.btn_segments_container = self._create_labeled_button("分段", "✂", self.segmentsToggleClicked, checkable=True)
        left_group.addWidget(self.btn_playlist_container)
        left_group.addWidget(self.btn_notes_container)
        left_group.addWidget(self.btn_segments_container)
        self.bottom_layout.addLayout(left_group)

        # --- 中左组: 颜色标记与分页 ---
        self.mark_group_widget = QWidget()
        self.mark_group_widget.setObjectName("markGroup")
        self.mark_group_widget.hide()
        mark_v_layout = QVBoxLayout(self.mark_group_widget)
        mark_v_layout.setContentsMargins(5, 0, 5, 0)
        mark_v_layout.setSpacing(4)
        
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(6)
        self.color_buttons = []
        colors = ["#ff4757", "#ffa502", "#2ed573", "#1e90ff", "#6c63ff", "#f368e0"]
        for color in colors:
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setObjectName("colorCircle")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("color", color) # 存储颜色
            btn.setStyleSheet(f"background-color: {color}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);")
            btn.clicked.connect(lambda checked, c=color: self.colorSelected.emit(c))
            btn.setFocusPolicy(Qt.NoFocus)
            colors_layout.addWidget(btn)
            self.color_buttons.append(btn)
        mark_v_layout.addLayout(colors_layout)

        pages_layout = QHBoxLayout()
        pages_layout.setSpacing(8)
        self.btn_page_prev = QPushButton("‹")
        self.btn_page_prev.setObjectName("actionButton")
        self.btn_page_prev.setFocusPolicy(Qt.NoFocus)
        self.btn_page_prev.clicked.connect(self.prevPageClicked.emit)
        self._scalable_buttons.append((self.btn_page_prev, 24, 16))
        
        self.label_page = QLabel("1/1")
        self.label_page.setObjectName("pageLabel")
        self.label_page.setStyleSheet("font-size: 10px; color: #6c63ff; font-weight: bold; min-width: 25px;")
        self.label_page.setAlignment(Qt.AlignCenter)
        self._scalable_labels.append((self.label_page, 10))
        
        self.btn_page_next = QPushButton("›")
        self.btn_page_next.setObjectName("actionButton")
        self.btn_page_next.setFocusPolicy(Qt.NoFocus)
        self.btn_page_next.clicked.connect(self.nextPageClicked.emit)
        self._scalable_buttons.append((self.btn_page_next, 24, 16))
        
        self.btn_new_page = QPushButton("+")
        self.btn_new_page.setObjectName("actionButton")
        self.btn_new_page.setStyleSheet("font-weight: bold; color: #6c63ff;")
        self.btn_new_page.setFocusPolicy(Qt.NoFocus)
        self.btn_new_page.clicked.connect(self.newPageClicked.emit)
        self._scalable_buttons.append((self.btn_new_page, 24, 16))
        
        pages_layout.addWidget(self.btn_page_prev)
        pages_layout.addWidget(self.label_page)
        pages_layout.addWidget(self.btn_page_next)
        pages_layout.addSpacing(6)
        pages_layout.addWidget(self.btn_new_page)
        mark_v_layout.addLayout(pages_layout)
        self.bottom_layout.addWidget(self.mark_group_widget)
        self.bottom_layout.addStretch(1)

        # --- 中间组: 核心媒体控制 ---
        self.media_group = QHBoxLayout()
        self.media_group.setSpacing(20)
        self._scalable_layouts.append((self.media_group, 0, 20))
        
        self.btn_prev = self._create_icon_button("⏮", self.prevClicked)
        self.btn_play = QPushButton("▶")
        self.btn_play.setObjectName("mainPlayButton")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setFocusPolicy(Qt.NoFocus)
        self.btn_play.clicked.connect(self.playPauseClicked.emit)
        self._scalable_buttons.append((self.btn_play, 64, 32))
        
        self.btn_next = self._create_icon_button("⏭", self.nextClicked)
        self.btn_stop = self._create_icon_button("⏹", self.stopClicked)
        self.media_group.addWidget(self.btn_prev)
        self.media_group.addWidget(self.btn_play)
        self.media_group.addWidget(self.btn_next)
        self.media_group.addWidget(self.btn_stop)
        self.bottom_layout.addLayout(self.media_group)
        self.bottom_layout.addStretch(1)

        # --- 中右组: 音量 & 倍速 ---
        right_mid_group = QHBoxLayout()
        right_mid_group.setSpacing(15)
        self.btn_volume = QPushButton("🔊")
        self.btn_volume.setObjectName("controlButton")
        self._scalable_buttons.append((self.btn_volume, 42, 22))
        self.btn_volume.clicked.connect(self.muteClicked.emit)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(70)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.valueChanged.connect(self.volumeChanged.emit)
        
        self.speed_combo = QComboBox()
        self.speed_combo.setObjectName("speedCombo")
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x", "3.0x"])
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.setFixedWidth(65)
        self.speed_combo.setFocusPolicy(Qt.NoFocus)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        
        right_mid_group.addWidget(self.btn_volume)
        right_mid_group.addWidget(self.volume_slider)
        right_mid_group.addWidget(self.speed_combo)
        self.bottom_layout.addLayout(right_mid_group)

        # --- 右侧组: 设置 & 全屏 ---
        right_group = QHBoxLayout()
        right_group.setSpacing(15)
        self.btn_snapshot_container = self._create_labeled_button("截屏", "📸", self.snapshotClicked)
        self.btn_settings_container = self._create_labeled_button("设置", "⚙", None)
        self.btn_fullscreen_container = self._create_labeled_button("全屏", "⛶", self.fullscreenToggleClicked)
        right_group.addWidget(self.btn_snapshot_container)
        right_group.addWidget(self.btn_settings_container)
        right_group.addWidget(self.btn_fullscreen_container)
        self.bottom_layout.addLayout(right_group)

        self.main_layout.addLayout(self.bottom_layout)
        self._setup_note_toolbar(self.main_layout)
        
        # 初始缩放
        self.scale_ui(1.0)

    def _create_labeled_button(self, text, icon, signal, checkable=False):
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)
        btn = QPushButton(icon)
        btn.setObjectName("controlButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        self._scalable_buttons.append((btn, 56, 28))
        
        if checkable:
            btn.setCheckable(True)
            if hasattr(signal, 'emit'):
                btn.clicked.connect(lambda checked: signal.emit(checked))
            else:
                btn.clicked.connect(signal)
        elif signal:
            if hasattr(signal, 'emit'):
                btn.clicked.connect(lambda: signal.emit())
            else:
                btn.clicked.connect(signal)
                
        label = QLabel(text)
        label.setObjectName("buttonLabel")
        label.setAlignment(Qt.AlignCenter)
        self._scalable_labels.append((label, 10))
        
        v_layout.addWidget(btn)
        v_layout.addWidget(label)
        
        if text == "播放列表": self.btn_playlist = btn
        if text == "书签": self.btn_notes = btn
        if text == "全屏": self.btn_fullscreen = btn
        if text == "设置": self.btn_settings = btn
        if text == "分段": self.btn_segments = btn
        return container

    def _create_icon_button(self, icon, signal):
        btn = QPushButton(icon)
        btn.setObjectName("controlButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        self._scalable_buttons.append((btn, 48, 24))
        if signal:
            btn.clicked.connect(signal.emit)
        return btn

    def _setup_note_toolbar(self, parent_layout):
        self.note_toolbar = QWidget()
        self.note_toolbar.setObjectName("noteToolbar")
        self.note_toolbar.hide()
        layout = QHBoxLayout(self.note_toolbar)
        layout.setContentsMargins(15, 5, 15, 5)
        
        self.btn_pen = self._create_tool_button("🖊", 'pen', True)
        self.btn_highlighter = self._create_tool_button("🖍", 'highlighter')
        self.btn_eraser = self._create_tool_button("🧽", 'eraser')
        self.btn_text = self._create_tool_button("A", 'text')
        
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(2, 20)
        self.width_slider.setValue(4)
        self.width_slider.setFixedWidth(80)
        self.width_slider.setFocusPolicy(Qt.NoFocus)
        self.width_slider.valueChanged.connect(self.penWidthChanged.emit)
        
        layout.addWidget(self.btn_pen)
        layout.addWidget(self.btn_highlighter)
        layout.addWidget(self.btn_eraser)
        layout.addWidget(self.btn_text)
        layout.addSpacing(10)
        layout.addWidget(self.width_slider)
        layout.addStretch(1)
        
        self.btn_undo = self._create_tool_button("↩", 'undo', is_action=True)
        self.btn_redo = self._create_tool_button("↪", 'redo', is_action=True)
        self.btn_clear = self._create_tool_button("🗑", 'clear', is_action=True)
        self.btn_aggregate = self._create_tool_button("🖼", 'aggregate', is_action=True)
        
        layout.addWidget(self.btn_undo)
        layout.addWidget(self.btn_redo)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_aggregate)
        parent_layout.insertWidget(0, self.note_toolbar)

    def _create_tool_button(self, icon, tool_name, checked=False, is_action=False):
        btn = QPushButton(icon)
        btn.setObjectName("toolButton")
        btn.setFocusPolicy(Qt.NoFocus)
        self._scalable_buttons.append((btn, 48, 24))
        if is_action:
            if tool_name == 'undo': btn.clicked.connect(self.undoClicked.emit)
            if tool_name == 'redo': btn.clicked.connect(self.redoClicked.emit)
            if tool_name == 'clear': btn.clicked.connect(self.clearNotesClicked.emit)
            if tool_name == 'aggregate': btn.clicked.connect(self.aggregateNotesClicked.emit)
        else:
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.clicked.connect(lambda: self._select_tool(tool_name))
        return btn

    def scale_ui(self, factor):
        """动态缩放 UI 组件"""
        # 1. 缩放按钮大小和字体
        for btn, base_size, base_font in self._scalable_buttons:
            size = int(base_size * factor)
            btn.setFixedSize(size, size)
            btn.setStyleSheet(f"font-size: {int(base_font * factor)}px;")
        
        # 2. 缩放标签字体
        for label, base_font in self._scalable_labels:
            label.setStyleSheet(f"font-size: {int(base_font * factor)}px;")
            
        # 3. 缩放间距和边距
        for layout, base_margin, base_spacing in self._scalable_layouts:
            if base_margin > 0:
                m = int(base_margin * factor)
                layout.setContentsMargins(m, int(m * 0.75), m, m)
            layout.setSpacing(int(base_spacing * factor))
            
        # 4. 颜色按钮缩放
        if hasattr(self, 'color_buttons'):
            c_size = int(16 * factor)
            for btn in self.color_buttons:
                btn.setFixedSize(c_size, c_size)
                color = btn.property("color")
                btn.setStyleSheet(f"background-color: {color}; border-radius: {c_size//2}px; border: 1px solid rgba(255,255,255,0.2);")
        
        # 5. 滑块高度
        if hasattr(self, 'progress_slider'):
            self.progress_slider.setFixedHeight(int(40 * factor))

    def update_position(self, position_ms):
        if not self._is_seeking:
            self.progress_slider.setValue(position_ms)
        self.label_time.setText(format_time(position_ms))

    def update_duration(self, duration_ms):
        self.progress_slider.setRange(0, duration_ms)
        self.label_duration.setText(format_time(duration_ms))

    def set_playing_state(self, is_playing):
        self.btn_play.setText("⏸" if is_playing else "▶")

    def set_mute_icon(self, is_muted):
        # 恢复符合直觉的 UI 逻辑：静音时显示静音图标，否则显示喇叭图标
        self.btn_volume.setText("🔇" if is_muted else "🔊")

    def reset(self):
        self.progress_slider.setValue(0)
        self.label_time.setText("00:00")
        self.label_duration.setText("00:00")

    def _on_slider_pressed(self): self._is_seeking = True
    def _on_slider_released(self):
        self._is_seeking = False
        self.seekRequested.emit(self.progress_slider.value())
    def _on_slider_moved(self, value): self.label_time.setText(format_time(value))
    def _on_speed_changed(self, text):
        rate = float(text.replace('x', ''))
        self.rateChanged.emit(rate)

    def _select_tool(self, tool):
        if hasattr(self, 'btn_pen'):
            self.btn_pen.setChecked(tool == 'pen')
            self.btn_highlighter.setChecked(tool == 'highlighter')
            self.btn_eraser.setChecked(tool == 'eraser')
            self.btn_text.setChecked(tool == 'text')
        self.toolSelected.emit(tool)

    def _on_notes_toggled(self, checked):
        self.note_toolbar.setVisible(checked)
        self.mark_group_widget.setVisible(checked)
        self.notesToggleClicked.emit(checked)
