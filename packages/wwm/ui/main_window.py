"""
Main Window for WWM Desktop Client

主窗口组件，包含应用的主要界面布局和功能区域。
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt, Signal, Slot

from ui.layout_window_title_bar import LayoutWindowTitleBar
from ui.layout_transparent import LayoutTransparent
from ui.layout_window_status_bar import LayoutWindowStatusBar
from runbooks.task import Task
from ui.containers.runbook_task_container import RunbookTaskContainer
from ui.containers.runbook_wloop_container import RunbookWLoopContainer
from ui.containers.runbook_bootstrap_container import RunbookBootstrapContainer


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals
    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = Task()
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("维维美")
        self.setMinimumSize(900, 400)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(0.4)

        central = QWidget()
        central.setAutoFillBackground(False)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(LayoutWindowTitleBar("维维美"))

        panels = QHBoxLayout()
        panels.setContentsMargins(0, 0, 0, 0)
        panels.setSpacing(0)

        # 左：50% 透明（alpha=128），绿边框
        self.bootstrap_panel = LayoutTransparent(128, "green")
        bootstrap_layout = QVBoxLayout(self.bootstrap_panel)

        self.bootstrap_container = RunbookBootstrapContainer(self)
        bootstrap_layout.addWidget(self.bootstrap_container)

        panels.addWidget(self.bootstrap_panel, stretch=2)

        # 中：50% 透明（alpha=128），红边框
        self.left_panel = LayoutTransparent(128, "red")
        left_layout = QVBoxLayout(self.left_panel)

        self.runbook_container = RunbookTaskContainer(self.task, self)
        left_layout.addWidget(self.runbook_container)

        panels.addWidget(self.left_panel, stretch=2)

        # 右：90% 透明（alpha=26），蓝边框
        self.right_panel = LayoutTransparent(26, "blue")
        right_layout = QVBoxLayout(self.right_panel)

        self.wloop_container = RunbookWLoopContainer(self)
        right_layout.addWidget(self.wloop_container)

        panels.addWidget(self.right_panel, stretch=3)

        root.addLayout(panels)

        self.status_bar = LayoutWindowStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_connections(self):
        """Connect signals and slots."""
        self.window_closing.connect(self._on_closing)

    @Slot()
    def _on_closing(self):
        """Handle window close event."""
        self.close()

    def update_status(self, message: str):
        """Update the status bar message.

        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)
