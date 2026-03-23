"""文件选择器组件"""

from typing import Callable, Optional

from loguru import logger
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
)
from PySide6.QtCore import QObject


class FileSelectorBuilder:
    """文件选择器组件构建器
    
    构建一个包含操作按钮、文件路径显示框的行布局。
    """

    # 样式常量
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 36
    TEXT_HEIGHT = 30
    SPACING = 8
    MARGINS = (20, 0, 20, 0)
    SPACER_WIDTH = 20

    def __init__(self):
        self.layout = None
        self.button = None
        self.value = None
        self._parent = None
        self._placeholder_text = ""
        self._working_directory = ""

    def build(
        self,
        parent: QObject,
        working_directory: str,
        default_value: Optional[str] = None,
        button_text: str = "选择文件",
        placeholder_text: str = "选择文件",
    ) -> QHBoxLayout:
        """构建文件选择器行布局
        
        Args:
            parent: 父窗口对象（用于 QFileDialog）
            working_directory: 文件对话框的初始目录
            default_value: 默认值（默认为空字符串）
            button_text: 操作按钮的文本
            placeholder_text: 文件对话框的标题
        
        Returns:
            QHBoxLayout: 完整的行布局
        """
        self._parent = parent
        self._placeholder_text = placeholder_text
        self._working_directory = working_directory
        if default_value is None:
            default_value = ""

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(*self.MARGINS)
        self.layout.setSpacing(self.SPACING)

        # 文件路径显示框（只读）
        self.value = QLineEdit(default_value)
        self.value.setReadOnly(True)
        self.value.setFixedHeight(self.TEXT_HEIGHT)
        self.value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.value)

        # 弹性空间
        spacer = QSpacerItem(
            self.SPACER_WIDTH,
            self.SPACER_WIDTH,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.layout.addSpacerItem(spacer)

        # 操作按钮（放在右边）
        self.button = QPushButton(button_text)
        self.button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.button.setProperty("class", "default")
        self.button.clicked.connect(self._on_select_file)
        self.layout.addWidget(self.button)

        return self.layout

    def get_value(self) -> str:
        """获取当前显示的值"""
        return self.value.text() if self.value else ""

    def set_value(self, value: str):
        """设置显示的值"""
        if self.value:
            self.value.setText(value)

    def set_working_directory(self, working_directory: str):
        """设置工作目录"""
        self._working_directory = working_directory

    def _on_select_file(self):
        """处理文件选择"""
        selected_file, _ = QFileDialog.getOpenFileName(
            self._parent,
            self._placeholder_text,
            self._working_directory,
        )
        if selected_file:
            # 计算相对路径
            if self._working_directory and selected_file.startswith(self._working_directory):
                relative_path = selected_file[len(self._working_directory):].lstrip("/\\")
            else:
                relative_path = selected_file
            self.value.setText(relative_path)
            logger.info(f"文件已选择: {relative_path}")
