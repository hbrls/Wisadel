"""
Solo Runner 组件

 ┌─ s1 ──┐
 │ 05:23 │
 └───────┘
"""

from string import Template

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, QObject, Signal


class SoloRunnerBuilder(QObject):
    """Solo Runner 组件构建器

    构建一个包含运行按钮和一个状态框的行布局。
    用于需要执行单个 prompt 并显示状态的场景。
    """

    run_requested = Signal()
    run_finished = Signal()

    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 36
    STATUS_BOX_WIDTH = 60
    STATUS_BOX_HEIGHT = 48
    SPACING = 8
    MARGINS = (20, 0, 20, 0)
    SPACER_WIDTH = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = None
        self.button = None
        self.status_boxes = []
        self.status_labels = []
        self.prompt = None
        self.working_directory = None

    def build(
        self,
        working_directory: str,
        session_ids: list[str],
        session_offset: int,
        prompt: Template,
        button_text: str = "Run",
        default_value: str = "--:--",
    ) -> QHBoxLayout:
        """构建 Solo Runner 行布局

        Args:
            working_directory: 工作目录路径
            session_ids: 会话 ID 列表
            session_offset: 会话偏移量
            prompt: 关联的 prompt Template 对象
            on_start_callback: 按钮点击时的回调函数
            on_end_callback: worker 完成时的回调函数
            button_text: 运行按钮的文本
            default_value: 状态框默认显示值

        Returns:
            QHBoxLayout: 完整的行布局
        """
        self.working_directory = working_directory

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(*self.MARGINS)
        self.layout.setSpacing(self.SPACING)

        self.button = QPushButton(button_text)

        def on_button_click():
            self.run_requested.emit()

        self.button.clicked.connect(on_button_click)
        self.button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.layout.addWidget(self.button)

        self.status_boxes = []
        self.status_labels = []
        runner_ids = ["s1"]
        for i in range(len(runner_ids)):
            title = runner_ids[i]
            group, label = self._create_status_box(title, default_value)
            self.status_boxes.append(group)
            self.status_labels.append(label)
            self.layout.addWidget(group)

        spacer = QSpacerItem(
            self.SPACER_WIDTH,
            self.SPACER_WIDTH,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.layout.addSpacerItem(spacer)

        return self.layout

    def _create_status_box(self, title: str, default_value: str) -> tuple[QGroupBox, QLabel]:
        """创建单个状态框

        Args:
            title: 状态框标题
            default_value: 默认显示值

        Returns:
            tuple: (QGroupBox, QLabel) 状态框和内部标签
        """
        group = QGroupBox(title)
        group.setFixedSize(self.STATUS_BOX_WIDTH, self.STATUS_BOX_HEIGHT)

        label = QLabel(default_value)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 2, 4, 4)
        layout.addWidget(label)

        return group, label

    def set_button_enabled(self, enabled: bool):
        """设置按钮启用状态"""
        if self.button:
            self.button.setEnabled(enabled)

    def set_status(self, index: int, value: str):
        """设置指定状态框的值

        Args:
            index: 状态框索引（从 0 开始）
            value: 要显示的值
        """
        if 0 <= index < len(self.status_labels):
            self.status_labels[index].setText(value)

    def reset_status(self, default_value: str = "--:--"):
        """重置所有状态框为默认值"""
        for label in self.status_labels:
            label.setText(default_value)

    def get_button(self) -> QPushButton:
        """获取按钮对象"""
        return self.button

    def set_working_directory(self, working_directory: str):
        """设置工作目录"""
        if self.working_directory == working_directory:
            return
        self.working_directory = working_directory
        print(f"[SoloRunnerBuilder] sync_working_directory: {working_directory}")

    def _on_worker_finished(self):
        """worker 完成回调"""
        self.run_finished.emit()