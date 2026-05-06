from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, FluentIcon as FIF

from ui.styles import SPACING
from ui.containers.runbook_task_container import RunbookTaskContainer


class TaskPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskPage")
        self.task_container = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("Task", self)
        layout.addWidget(title)

        self.task_container = RunbookTaskContainer(self)
        layout.addWidget(self.task_container, stretch=1)
