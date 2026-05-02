"""文件选择器组件"""

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


class FileSelectorBuilder(QObject):
    """文件选择器组件构建器

    构建一个包含文件选择按钮、路径显示框的行布局。
    """

    file_changed = Signal(str)

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
        self._base_directory = ""

    def build(
        self,
        parent: QObject,
        default_value: Optional[str] = None,
        button_text: str = "选择文件",
        placeholder_text: str = "选择文件",
        file_filter: str = "所有文件 (*)",
    ) -> QHBoxLayout:
        """构建文件选择器行布局

        Args:
            parent: 父窗口对象（用于 QFileDialog）
            get_working_directory: 获取当前工作目录的 callable，按需调用
            on_select_callback: 文件选择后的回调函数，接收选中的路径
            default_value: 默认路径
            button_text: 选择按钮的文本
            placeholder_text: 文件对话框的标题
            file_filter: 文件类型过滤器
            get_file_path: 获取当前文件路径的 callable，用于决定文件对话框的起始目录

        Returns:
            QHBoxLayout: 完整的行布局
        """
        if default_value is None:
            default_value = ""

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(*self.MARGINS)
        self.layout.setSpacing(self.SPACING)

        self.button = QPushButton(button_text)
        self.button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.button.clicked.connect(
            lambda: self._on_select_file(
                parent, placeholder_text, file_filter
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

    def _on_select_file(
        self,
        parent: QObject,
        placeholder_text: str,
        file_filter: str,
    ):
        """处理文件选择"""
        start_dir = None

        current_file = self.get_value()
        if current_file:
            absolute_file = os.path.join(self._base_directory, current_file)
            if os.path.isfile(absolute_file):
                start_dir = os.path.dirname(absolute_file)

        if not start_dir:
            start_dir = self._base_directory if os.path.isdir(self._base_directory) else os.path.expanduser("~")

        selected_file, _ = QFileDialog.getOpenFileName(
            parent,
            placeholder_text,
            start_dir,
            file_filter,
        )
        if selected_file:
            self.value.setText(selected_file)
            self.file_changed.emit(selected_file)

    def get_value(self) -> str:
        """获取当前显示的路径"""
        return self.value.text() if self.value else ""

    def set_base_directory(self, directory: str):
        """更新文件选择器的基准目录（供 Controller 调用）"""
        self._base_directory = directory

    def set_value(self, path: str):
        """设置显示的路径"""
        if self.value:
            self.value.setText(path)
