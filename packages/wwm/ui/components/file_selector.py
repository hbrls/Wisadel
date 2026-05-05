"""Fluent 风格的文件选择器组件"""

import os
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFileDialog
from qfluentwidgets import LineEdit, ToolButton, FluentIcon as FIF

from ui.styles import SPACING


class FileSelector(QWidget):
    """Fluent 风格的文件选择器组件
    
    作为受控组件使用，提供：
    - value(): 获取当前显示的文件路径（相对路径）
    - set_value(path): 静默同步文件路径（相对路径），不触发 file_changed
    - set_base_directory(directory): 设置工作目录基准
    - file_changed: 用户主动选择文件时发出的信号（发出相对路径）
    """

    file_changed = Signal(str)

    BUTTON_SIZE = 33

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        button_text: str = "选择文件",
        placeholder_text: str = "选择文件",
        file_filter: str = "所有文件 (*)",
    ):
        super().__init__(parent)
        self._button_text = button_text
        self._placeholder_text = placeholder_text
        self._file_filter = file_filter
        self._base_directory = ""
        self._current_file = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        self._path_edit = LineEdit(self)
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText(self._placeholder_text)
        self._path_edit.setFixedHeight(self.BUTTON_SIZE)
        self._path_edit.setClearButtonEnabled(False)
        layout.addWidget(self._path_edit, stretch=1)

        self._browse_button = ToolButton(FIF.DOCUMENT, self)
        self._browse_button.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self._browse_button.setToolTip(self._button_text)
        self._browse_button.clicked.connect(self._on_browse)
        layout.addWidget(self._browse_button)

    def _on_browse(self):
        start_dir = self._base_directory if os.path.isdir(self._base_directory) else os.path.expanduser("~")

        if self._current_file:
            absolute_file = os.path.join(self._base_directory, self._current_file)
            if os.path.isfile(absolute_file):
                start_dir = os.path.dirname(absolute_file)

        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            self._placeholder_text,
            start_dir,
            self._file_filter,
        )
        if selected_file:
            relative_path = self._to_relative_path(selected_file)
            self._current_file = relative_path
            self._path_edit.setText(relative_path)
            self.file_changed.emit(relative_path)

    def _to_relative_path(self, absolute_path: str) -> str:
        if self._base_directory and absolute_path.startswith(self._base_directory):
            return absolute_path[len(self._base_directory):].lstrip("/\\")
        return absolute_path

    def value(self) -> str:
        return self._current_file

    def get_value(self) -> str:
        return self.value()

    def set_value(self, path: str):
        self._current_file = path
        self._path_edit.setText(path)

    def set_base_directory(self, directory: str):
        self._base_directory = directory