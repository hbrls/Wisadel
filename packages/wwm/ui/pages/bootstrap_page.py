from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, FluentIcon as FIF

from ui.styles import SPACING
from ui.containers.combo_bootstrap_container import ComboBootstrapContainer


class BootstrapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BootstrapPage")
        self.bootstrap_container = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("Bootstrap", self)
        layout.addWidget(title)

        self.bootstrap_container = ComboBootstrapContainer(self)
        layout.addWidget(self.bootstrap_container, stretch=1)
