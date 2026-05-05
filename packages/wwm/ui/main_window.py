"""
Main Window for WWM Desktop Client

主窗口组件，包含应用的主要界面布局和功能区域。
"""

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStatusBar
from qfluentwidgets import FluentWidget

from runbooks.task import Task
from ui.containers.runbook_task_container import RunbookTaskContainer
from ui.containers.runbook_wloop_container import RunbookWLoopContainer
from ui.containers.runbook_bootstrap_container import RunbookBootstrapContainer


class MainWindow(FluentWidget):
    """Main application window."""

    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = Task()
        self._setup_window()
        self._setup_ui()
        self._setup_connections()

    def _setup_window(self):
        self.setWindowTitle("维维美")
        self.setMinimumSize(900, 400)
        self.setMicaEffectEnabled(False)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, self.titleBar.height(), 0, 0)
        root.setSpacing(0)

        red_line = QWidget()
        red_line.setFixedHeight(4)
        red_line.setStyleSheet("background-color: red;")
        root.addWidget(red_line)

        panels = QHBoxLayout()
        panels.setContentsMargins(0, 0, 0, 0)
        panels.setSpacing(0)

        self.bootstrap_panel = QWidget()
        self.bootstrap_panel.setStyleSheet("border: 3px solid green;")
        bootstrap_layout = QVBoxLayout(self.bootstrap_panel)

        self.bootstrap_container = RunbookBootstrapContainer(self)
        bootstrap_layout.addWidget(self.bootstrap_container)

        panels.addWidget(self.bootstrap_panel, stretch=2)

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("border: 3px solid red;")
        left_layout = QVBoxLayout(self.left_panel)

        self.runbook_container = RunbookTaskContainer(self.task, self)
        left_layout.addWidget(self.runbook_container)

        panels.addWidget(self.left_panel, stretch=2)

        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("border: 3px solid blue;")
        right_layout = QVBoxLayout(self.right_panel)

        self.wloop_container = RunbookWLoopContainer(self)
        right_layout.addWidget(self.wloop_container)

        panels.addWidget(self.right_panel, stretch=3)

        root.addLayout(panels)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        root.addWidget(self.status_bar)

    def _setup_connections(self):
        self.window_closing.connect(self._on_closing)

    @Slot()
    def _on_closing(self):
        self.close()

    def update_status(self, message: str):
        self.status_bar.showMessage(message)
