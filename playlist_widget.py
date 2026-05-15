"""侧边栏播放列表组件"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMenu, QAction,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from utils import get_filename, is_video_file


class PlaylistWidget(QWidget):
    """侧边栏播放列表"""

    fileSelected = pyqtSignal(str)  # 选中播放文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playlistPanel")
        self.setFixedWidth(280)
        self._files = []  # 存储文件路径列表
        self._current_index = -1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = QWidget()
        header.setObjectName("playlistHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 8, 8)

        title = QLabel("📋 播放列表")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setStyleSheet("color: #c0c0d0; background: transparent; border: none;")

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("playlistToggleBtn")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setFocusPolicy(Qt.NoFocus)
        self.btn_close.setToolTip("关闭播放列表")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("playlistWidget")
        self.list_widget.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.doubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        # 允许拖拽文件到列表
        self.list_widget.setAcceptDrops(True)
        self.list_widget.dragEnterEvent = self._drag_enter
        self.list_widget.dropEvent = self._drop_event

        layout.addWidget(self.list_widget)

        # 底部按钮
        bottom = QWidget()
        bottom.setStyleSheet("background-color: #16163a; border-top: 1px solid #2a2a4a;")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 6, 8, 6)

        self.btn_add = QPushButton("＋ 添加文件")
        self.btn_add.setObjectName("controlButton")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: rgba(108, 99, 255, 0.2);
                border: 1px solid rgba(108, 99, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                color: #a0a0d0;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(108, 99, 255, 0.4);
                color: #ffffff;
            }
        """)
        self.btn_add.setFocusPolicy(Qt.NoFocus)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("controlButton")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 80, 80, 0.15);
                border: 1px solid rgba(255, 80, 80, 0.2);
                border-radius: 6px;
                padding: 6px 12px;
                color: #a08080;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 80, 80, 0.3);
                color: #ff8080;
            }
        """)
        self.btn_clear.setFocusPolicy(Qt.NoFocus)
        self.btn_clear.clicked.connect(self.clear_playlist)

        bottom_layout.addWidget(self.btn_add)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_clear)

        layout.addWidget(bottom)

    def add_file(self, filepath):
        """添加单个文件到播放列表"""
        if filepath not in self._files:
            self._files.append(filepath)
            item = QListWidgetItem(get_filename(filepath))
            item.setData(Qt.UserRole, filepath)
            item.setToolTip(filepath)
            self.list_widget.addItem(item)

    def add_files(self, filepaths):
        """批量添加文件"""
        for fp in filepaths:
            self.add_file(fp)

    def clear_playlist(self):
        """清空播放列表"""
        self._files.clear()
        self.list_widget.clear()
        self._current_index = -1

    def get_current_file(self):
        """获取当前选中的文件"""
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None

    def set_current_index(self, index):
        """设置当前播放索引"""
        if 0 <= index < len(self._files):
            self._current_index = index
            self.list_widget.setCurrentRow(index)

    def highlight_file(self, filepath):
        """高亮指定文件"""
        for i, fp in enumerate(self._files):
            if fp == filepath:
                self._current_index = i
                self.list_widget.setCurrentRow(i)
                break

    def get_next_file(self):
        """获取下一个文件"""
        if len(self._files) == 0:
            return None
        next_index = self._current_index + 1
        if next_index >= len(self._files):
            next_index = 0  # 循环播放
        self._current_index = next_index
        self.list_widget.setCurrentRow(next_index)
        return self._files[next_index]

    def get_prev_file(self):
        """获取上一个文件"""
        if len(self._files) == 0:
            return None
        prev_index = self._current_index - 1
        if prev_index < 0:
            prev_index = len(self._files) - 1
        self._current_index = prev_index
        self.list_widget.setCurrentRow(prev_index)
        return self._files[prev_index]

    def file_count(self):
        """获取文件总数"""
        return len(self._files)

    def _on_item_double_clicked(self, index):
        """双击项目播放"""
        row = index.row()
        if 0 <= row < len(self._files):
            self._current_index = row
            self.fileSelected.emit(self._files[row])

    def _show_context_menu(self, pos):
        """右键菜单"""
        item = self.list_widget.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self)
        action_play = QAction("▶ 播放", self)
        action_remove = QAction("✕ 从列表移除", self)
        action_clear = QAction("🗑 清空列表", self)

        menu.addAction(action_play)
        menu.addSeparator()
        menu.addAction(action_remove)
        menu.addAction(action_clear)

        action = menu.exec_(self.list_widget.mapToGlobal(pos))

        if action == action_play:
            row = self.list_widget.row(item)
            self._current_index = row
            self.fileSelected.emit(self._files[row])
        elif action == action_remove:
            row = self.list_widget.row(item)
            self._files.pop(row)
            self.list_widget.takeItem(row)
            if self._current_index >= len(self._files):
                self._current_index = len(self._files) - 1
        elif action == action_clear:
            self.clear_playlist()

    def _drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop_event(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            filepath = url.toLocalFile()
            if os.path.isfile(filepath) and is_video_file(filepath):
                self.add_file(filepath)
            elif os.path.isdir(filepath):
                from utils import get_video_files_from_dir
                self.add_files(get_video_files_from_dir(filepath))
