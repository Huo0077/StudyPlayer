"""暗色主题 QSS 样式表"""

DARK_THEME = """
/* ============ 全局基础设置 ============ */
QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0b0b1a;
}

QWidget {
    color: #e2e2ee;
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    outline: none;
}

/* ============ 玻璃拟态控制栏 (Glassmorphism) ============ */
#controlsContainer {
    background-color: rgba(20, 20, 40, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    margin: 15px;
}

/* ============ 播放器中心提示 (Empty State) ============ */
#hintLabel {
    color: #8888a0;
    font-size: 16px;
    font-weight: 500;
}

#openFileButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6c63ff, stop:1 #4f46e5);
    color: white;
    border-radius: 12px;
    padding: 10px 25px;
    font-weight: bold;
    font-size: 14px;
}

#openFileButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7d75ff, stop:1 #5d54f5);
}

/* ============ 进度条 & 音量条 (Sleek Sliders) ============ */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6c63ff, stop:1 #a855f7);
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #6c63ff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}

/* ============ 按钮系统 ============ */
#controlButton, #actionButton, #toolButton {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #b1b1cc;
    border-radius: 16px;
    transition: all 0.2s ease;
}

#controlButton:hover, #actionButton:hover, #toolButton:hover {
    background-color: rgba(108, 99, 255, 0.12);
    border-color: rgba(108, 99, 255, 0.3);
    color: #ffffff;
    margin-top: -2px; /* 悬停微向上浮动 */
}

#controlButton:pressed, #actionButton:pressed {
    background-color: rgba(108, 99, 255, 0.25);
    margin-top: 1px; /* 点击下压感 */
}

#controlButton:checked, #toolButton:checked {
    background-color: rgba(108, 99, 255, 0.25);
    border-color: #6c63ff;
    color: #ffffff;
    box-shadow: 0 0 15px rgba(108, 99, 255, 0.3);
}

/* 核心播放按钮 - 特殊动态效果 */
#mainPlayButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6c63ff, stop:1 #a855f7);
    color: white;
    border: none;
    border-radius: 32px; /* 完美圆 */
}

#mainPlayButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7d75ff, stop:1 #b766ff);
    box-shadow: 0 0 25px rgba(108, 99, 255, 0.6);
}

#mainPlayButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7d75ff, stop:1 #b766ff);
}

/* 标签文字 (按钮下方的说明) */
#buttonLabel {
    font-size: 11px;
    color: #8888a0;
    margin-top: 2px;
}

/* ============ 笔记工具栏 ============ */
#noteToolbar {
    background-color: rgba(15, 15, 30, 0.85);
    border-radius: 15px;
    margin-bottom: 5px;
}

#colorCircle {
    border: 2px solid rgba(255, 255, 255, 0.2);
}
#colorCircle:hover {
    border-color: white;
}

/* ============ 下拉框 (ComboBox) ============ */
QComboBox {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 2px 10px;
    color: #e2e2ee;
}

QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #121225;
    border: 1px solid #2a2a45;
    selection-background-color: #6c63ff;
    color: #e2e2ee;
    outline: none;
}

/* ============ 菜单栏与下拉菜单 (Dark Menu) ============ */
QMenuBar {
    background-color: #0a0a1a;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #a1a1aa;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}

QMenu {
    background-color: #121225;
    border: 1px solid #2a2a45;
    border-radius: 8px;
    color: #e2e2ee;
    padding: 5px;
}

QMenu::item {
    padding: 8px 30px 8px 20px;
    border-radius: 4px;
    margin: 2px 0;
}

QMenu::item:selected {
    background-color: #6c63ff;
    color: white;
}

QMenu::separator {
    height: 1px;
    background: #2a2a45;
    margin: 5px 10px;
}

/* ============ 列表与侧边栏 ============ */
QListWidget {
    background-color: #0d0d1a;
    border-radius: 12px;
    border: none;
}

QListWidget::item {
    padding: 10px;
    border-radius: 8px;
    color: #a1a1aa;
}

QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

QListWidget::item:selected {
    background-color: rgba(108, 99, 255, 0.15);
    color: #6c63ff;
    font-weight: bold;
}
"""



