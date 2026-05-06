from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, FluentIcon as FIF

from ui.styles import SPACING
from ui.containers.combo_plan_container import ComboPlanContainer


class PlanPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlanPage")
        self.plan_container = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("Plan", self)
        layout.addWidget(title)

        self.plan_container = ComboPlanContainer(self)
        layout.addWidget(self.plan_container, stretch=1)