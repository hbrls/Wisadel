"""目录选择器组件"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
)
from PySide6.QtCore import QObject, Signal


class DirectorySelectorBuilder(QObject):
    """目录选择器组件构建器

    构建一个包含目录选择按钮、路径显示框的行布局。
    """

    directory_changed = Signal(str)

    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 36
    TEXT_HEIGHT = 30
    SPACING = 8
    MARGINS = (20, 0, 20, 0)
    SPACER_WIDTH = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = None
        self.button = None
        self.value = None

    def build(
        self,
        parent: QObject,
        default_value: Optional[str] = None,
        button_text: str = "选择目录",
        placeholder_text: str = "选择目录",
    ) -> QHBoxLayout:
        """构建目录选择器行布局

        Args:
            parent: 父窗口对象（用于 QFileDialog）
            on_select_callback: 目录选择后的回调函数，接收选中的路径
            default_value: 默认路径（默认为用户主目录）
            button_text: 选择按钮的文本
            placeholder_text: 文件对话框的标题

        Returns:
            QHBoxLayout: 完整的行布局
        """
        if default_value is None:
            default_value = os.path.expanduser("~")

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(*self.MARGINS)
        self.layout.setSpacing(self.SPACING)

        self.button = QPushButton(button_text)
        self.button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.button.clicked.connect(
            lambda: self._on_select_directory(
                parent, default_value, placeholder_text
            )
        )
        self.layout.addWidget(self.button)

        self.value = QLineEdit(default_value)
        self.value.setReadOnly(True)
        self.value.setFixedHeight(self.TEXT_HEIGHT)
        self.value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.value)

        spacer = QSpacerItem(
            self.SPACER_WIDTH,
            self.SPACER_WIDTH,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.layout.addSpacerItem(spacer)

        return self.layout

    def _on_select_directory(
        self,
        parent: QObject,
        initial_path: str,
        placeholder_text: str,
    ):
        """处理目录选择"""
        selected_dir = QFileDialog.getExistingDirectory(
            parent,
            placeholder_text,
            initial_path,
            QFileDialog.Option.ShowDirsOnly,
        )
        if selected_dir:
            self.value.setText(selected_dir)
            self.directory_changed.emit(selected_dir)

    def get_value(self) -> str:
        """获取当前显示的路径"""
        return self.value.text() if self.value else ""

    def set_value(self, path: str):
        """设置显示的路径"""
        if self.value:
            self.value.setText(path)
