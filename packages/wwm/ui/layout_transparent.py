"""
Layout Transparent Panel for WWM Desktop Client

半透明面板组件：自绘背景色（含 alpha）+ 彩色边框，子组件可正常添加。
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen


class LayoutTransparent(QWidget):
    """半透明面板组件：自绘背景色（含 alpha）+ 彩色边框，子组件可正常添加"""

    def __init__(self, alpha: int, border_color: str, parent=None):
        super().__init__(parent)
        self._alpha = alpha
        self._border_color = QColor(border_color)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(245, 245, 245, self._alpha))
        painter.setPen(QPen(self._border_color, 3))
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
