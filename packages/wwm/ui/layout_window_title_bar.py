"""
Layout Window Title Bar for WWM Desktop Client

自定义标题栏组件：支持拖动，带最小化和关闭按钮。
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont


class LayoutWindowTitleBar(QWidget):
    """自定义标题栏：支持拖动，带最小化和关闭按钮"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel(title)
        font = QFont()
        font.setPointSize(10)
        label.setFont(font)
        label.setStyleSheet("color: #1a1a1a;")
        layout.addWidget(label)
        layout.addStretch()

        min_btn = QPushButton("–")
        min_btn.setFixedSize(46, 32)
        min_btn.setStyleSheet("QPushButton { background: transparent; color: #1a1a1a; border: none; font-size: 14px; }"
                              "QPushButton:hover { background: rgba(0,0,0,15); }")
        min_btn.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(46, 32)
        close_btn.setStyleSheet("QPushButton { background: transparent; color: #1a1a1a; border: none; font-size: 12px; }"
                                "QPushButton:hover { background: #c42b1c; color: white; }")
        close_btn.clicked.connect(lambda: self.window().close())
        layout.addWidget(close_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 255))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
