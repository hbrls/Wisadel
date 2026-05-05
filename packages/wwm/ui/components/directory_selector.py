"""Fluent 风格的目录选择器组件"""

import os
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFileDialog
from qfluentwidgets import LineEdit, ToolButton, FluentIcon as FIF

from ui.styles import SPACING


class DirectorySelector(QWidget):
    """Fluent 风格的目录选择器组件
    
    作为受控组件使用，提供：
    - value(): 获取当前显示的路径
    - set_value(path): 静默同步路径，不触发 directory_changed
    - directory_changed: 用户主动选择目录时发出的信号
    """

    directory_changed = Signal(str)

    BUTTON_SIZE = 33

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        button_text: str = "选择目录",
        placeholder_text: str = "选择工作目录",
    ):
        super().__init__(parent)
        self._button_text = button_text
        self._placeholder_text = placeholder_text
        self._current_path = ""
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

        self._browse_button = ToolButton(FIF.FOLDER, self)
        self._browse_button.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self._browse_button.setToolTip(self._button_text)
        self._browse_button.clicked.connect(self._on_browse)
        layout.addWidget(self._browse_button)

    def _on_browse(self):
        initial_path = self._current_path if self._current_path else os.path.expanduser("~")
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            self._placeholder_text,
            initial_path,
            QFileDialog.Option.ShowDirsOnly,
        )
        if selected_dir:
            self._current_path = selected_dir
            self._path_edit.setText(selected_dir)
            self.directory_changed.emit(selected_dir)

    def value(self) -> str:
        return self._current_path

    def get_value(self) -> str:
        return self.value()

    def set_value(self, path: str):
        self._current_path = path
        self._path_edit.setText(path)