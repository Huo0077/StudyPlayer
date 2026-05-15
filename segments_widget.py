"""视频分段管理组件"""

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from utils import format_time

class SegmentItem(QWidget):
    """分段列表项 UI"""
    def __init__(self, name, start_ms, end_ms, parent=None):
        super().__init__(parent)
        self.setObjectName("segmentItem")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        
        time_text = f"{format_time(start_ms)} - {format_time(end_ms)}"
        self.time_label = QLabel(time_text)
        self.time_label.setStyleSheet("color: #8080a0; font-size: 11px;")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.time_label)

class SegmentsWidget(QWidget):
    """分段管理侧边栏"""

    segmentSelected = pyqtSignal(int, int)  # 发射 (start_ms, end_ms)
    addSegmentRequested = pyqtSignal(str)     # 发射分段名称
    segmentsChanged = pyqtSignal(list)        # 当列表变化（删除等）时发射

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("segmentsPanel")
        self.setFixedWidth(280)
        self._segments = [] # 列表项格式: {"name": str, "start": int, "end": int}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = QWidget()
        header.setObjectName("segmentsHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("🎬 视频分段")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setStyleSheet("color: #c0c0d0; background: transparent;")
        
        header_layout.addWidget(title)
        layout.addWidget(header)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("playlistWidget") # 复用样式
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        # 底部操作区 (创建新分段)
        bottom = QWidget()
        bottom.setStyleSheet("background-color: #0f0f25; border-top: 1px solid #1a1a3a;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 12, 12, 12)
        bottom_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入分段名称...")
        
        self.btn_add = QPushButton("保存当前选择范围")
        self.btn_add.setObjectName("playButton") # 复用主按钮样式
        self.btn_add.setStyleSheet("min-height: 40px; border-radius: 20px; font-size: 13px;")
        self.btn_add.setFocusPolicy(Qt.NoFocus)
        self.btn_add.clicked.connect(self._on_add_clicked)

        bottom_layout.addWidget(self.name_input)
        bottom_layout.addWidget(self.btn_add)
        layout.addWidget(bottom)

    def set_segments(self, segments):
        """设置并刷新分段列表"""
        self._segments = segments
        self.list_widget.clear()
        for seg in self._segments:
            item = QListWidgetItem(self.list_widget)
            custom_widget = SegmentItem(seg["name"], seg["start"], seg["end"])
            item.setSizeHint(custom_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, custom_widget)

    def add_segment(self, name, start, end):
        """添加一个分段并保存"""
        new_seg = {"name": name, "start": start, "end": end}
        self._segments.append(new_seg)
        self.set_segments(self._segments)
        self.name_input.clear()
        return self._segments

    def get_segments(self):
        return self._segments

    def _on_add_clicked(self):
        name = self.name_input.text().strip()
        if not name:
            name = f"未命名分段 {len(self._segments) + 1}"
        self.addSegmentRequested.emit(name)

    def _on_item_double_clicked(self, item):
        row = self.list_widget.row(item)
        if 0 <= row < len(self._segments):
            seg = self._segments[row]
            self.segmentSelected.emit(seg["start"], seg["end"])

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        
        menu = QMenu(self)
        del_action = QAction("🗑 删除分段", self)
        menu.addAction(del_action)
        
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == del_action:
            row = self.list_widget.row(item)
            self._segments.pop(row)
            self.set_segments(self._segments)
            self.segmentsChanged.emit(self._segments)
