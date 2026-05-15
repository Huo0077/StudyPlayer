"""透明笔记画布组件 - V5 增强型绘图引擎"""

from PyQt5.QtWidgets import QWidget, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QImage, QPainterPath


class NoteCanvas(QWidget):
    """覆盖在视频上的透明绘图板"""

    def __init__(self, parent=None):
        super().__init__(None)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        
        self.setMouseTracking(True)
        self.hide()

        self.mouse_move_callback = None

        self.current_tool = 'pen' 
        self.current_color = QColor("#ff4757")
        self.pen_width = 4

        self.pages = [self._create_empty_page()]
        self.current_page_index = 0
        
        self._current_path = None
        self._last_point = QPoint()

    def _create_empty_page(self):
        return {
            "strokes": [],
            "texts": [],
            "history": [],
            "redo_stack": []
        }

    @property
    def current_page(self):
        return self.pages[self.current_page_index]

    def new_page(self):
        self.pages.append(self._create_empty_page())
        self.current_page_index = len(self.pages) - 1
        self.update()

    def next_page(self):
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.update()
            return True
        return False

    def prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.update()
            return True
        return False

    def get_page_info(self):
        return self.current_page_index + 1, len(self.pages)

    def set_tool(self, tool):
        self.current_tool = tool
        self.update()

    def set_color(self, color_hex):
        self.current_color = QColor(color_hex)

    def set_pen_width(self, width):
        self.pen_width = width

    def clear_canvas(self):
        page = self.current_page
        page["strokes"] = []
        page["texts"] = []
        page["history"] = []
        page["redo_stack"] = []
        self.update()

    def undo(self):
        page = self.current_page
        if page["history"]:
            page["history"].pop()
            self._rebuild_from_history()
            self.update()

    def redo(self):
        # 简化版暂不实现完全重做
        pass

    def _rebuild_from_history(self):
        page = self.current_page
        page["strokes"] = []
        page["texts"] = []
        for op in page["history"]:
            if op["type"] == "stroke":
                page["strokes"].append(op["data"])
            elif op["type"] == "text":
                page["texts"].append(op["data"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 基础层：极其微弱的透明度以捕获鼠标，同时保持视频可见
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        
        page = self.current_page

        # 1. 绘制已保存的笔触
        for stroke in page["strokes"]:
            self._draw_stroke(painter, stroke)

        # 2. 绘制当前正在画的路径
        if self._current_path:
            current_stroke = {
                "path": self._current_path,
                "color": self.current_color,
                "width": self.pen_width,
                "type": self.current_tool
            }
            self._draw_stroke(painter, current_stroke)

        # 3. 绘制文字
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        for item in page["texts"]:
            painter.setPen(QColor(item["color"]))
            painter.drawText(item["pos"], item["text"])

    def _draw_stroke(self, painter, stroke):
        stype = stroke.get("type", "pen")
        width = stroke["width"]
        color = QColor(stroke["color"])
        
        if stype == "eraser":
            # 橡皮擦模式：使用 Clear 模式冲掉所有颜色
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.transparent, width * 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        elif stype == "highlighter":
            # 荧光笔模式：半透明、宽笔触、方头
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            color.setAlpha(80) 
            pen = QPen(color, width * 6, Qt.SolidLine, Qt.FlatCap, Qt.RoundJoin)
        else:
            # 普通笔：实色、圆头
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        
        painter.setPen(pen)
        painter.drawPath(stroke["path"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_tool in ['pen', 'eraser', 'highlighter']:
                self._current_path = QPainterPath()
                self._current_path.moveTo(event.pos())
                self._last_point = event.pos()
            elif self.current_tool == 'text':
                self._add_text(event.pos())

    def mouseMoveEvent(self, event):
        # 即使没有按下左键，也触发回调（通知主窗口显示控制栏）
        if self.mouse_move_callback:
            self.mouse_move_callback()

        if event.buttons() & Qt.LeftButton and self._current_path:
            new_point = event.pos()
            # 荧光笔和橡皮擦使用直线以提高性能并避免视觉重叠异常
            if self.current_tool in ['highlighter', 'eraser']:
                self._current_path.lineTo(new_point)
            else:
                # 普通笔使用平滑曲线
                mid_point = (self._last_point + new_point) / 2
                self._current_path.quadTo(self._last_point, mid_point)
            self._last_point = new_point
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._current_path:
            page = self.current_page
            stroke = {
                "path": self._current_path,
                "color": self.current_color.name(),
                "width": self.pen_width,
                "type": self.current_tool
            }
            page["strokes"].append(stroke)
            page["history"].append({"type": "stroke", "data": stroke})
            self._current_path = None
            self.update()

    def _add_text(self, pos):
        text, ok = QInputDialog.getText(self, "添加标注", "输入笔记内容:", QLineEdit.Normal, "")
        if ok and text:
            page = self.current_page
            item = {"text": text, "pos": pos, "color": self.current_color.name()}
            page["texts"].append(item)
            page["history"].append({"type": "text", "data": item})
            self.update()

    def get_notes_data(self):
        """将笔记数据转换为可序列化的字典"""
        data = []
        for page in self.pages:
            serialized_page = {
                "strokes": [],
                "texts": []
            }
            for s in page["strokes"]:
                # 序列化 QPainterPath
                path_data = []
                for i in range(s["path"].elementCount()):
                    el = s["path"].elementAt(i)
                    path_data.append((el.type, el.x, el.y))
                
                serialized_page["strokes"].append({
                    "path_elements": path_data,
                    "color": s["color"],
                    "width": s["width"],
                    "type": s["type"]
                })
            
            for t in page["texts"]:
                serialized_page["texts"].append({
                    "text": t["text"],
                    "x": t["pos"].x(),
                    "y": t["pos"].y(),
                    "color": t["color"]
                })
            data.append(serialized_page)
        return data

    def load_notes_data(self, data):
        """从字典加载笔记数据"""
        if not data or not isinstance(data, list):
            self.pages = [self._create_empty_page()]
            self.current_page_index = 0
            return

        self.pages = []
        for pdata in data:
            page = self._create_empty_page()
            for sdata in pdata.get("strokes", []):
                path = QPainterPath()
                elements = sdata.get("path_elements", [])
                if elements:
                    for etype, x, y in elements:
                        if etype == 0: # MoveTo
                            path.moveTo(x, y)
                        elif etype == 1: # LineTo
                            path.lineTo(x, y)
                        elif etype == 2: # CurveTo (not handled fully here for simplicity)
                            path.lineTo(x, y) # Fallback
                
                stroke = {
                    "path": path,
                    "color": sdata["color"],
                    "width": sdata["width"],
                    "type": sdata["type"]
                }
                page["strokes"].append(stroke)
                page["history"].append({"type": "stroke", "data": stroke})
            
            for tdata in pdata.get("texts", []):
                item = {
                    "text": tdata["text"],
                    "pos": QPoint(tdata["x"], tdata["y"]),
                    "color": tdata["color"]
                }
                page["texts"].append(item)
                page["history"].append({"type": "text", "data": item})
            self.pages.append(page)
        
        self.current_page_index = 0
        self.update()

    def get_combined_image(self, size):
        """生成所有页面的组合长图"""
        if not self.pages:
            return QImage(size, QImage.Format_ARGB32_Premultiplied)
            
        total_height = size.height() * len(self.pages)
        combined = QImage(size.width(), total_height, QImage.Format_ARGB32_Premultiplied)
        combined.fill(Qt.transparent)
        
        painter = QPainter(combined)
        for i, page in enumerate(self.pages):
            painter.save()
            painter.translate(0, i * size.height())
            
            # 绘制该页内容
            for stroke in page["strokes"]:
                self._draw_stroke(painter, stroke)
            
            painter.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
            for item in page["texts"]:
                painter.setPen(QColor(item["color"]))
                painter.drawText(item["pos"], item["text"])
            
            painter.restore()
            # 绘制分隔线
            if i < len(self.pages) - 1:
                painter.setPen(QPen(QColor(255, 255, 255, 50), 1, Qt.DashLine))
                painter.drawLine(0, (i+1)*size.height(), size.width(), (i+1)*size.height())
        
        painter.end()
        return combined
