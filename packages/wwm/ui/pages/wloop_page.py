from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, FluentIcon as FIF

from ui.styles import SPACING
from ui.containers.combo_wloop_container import ComboWLoopContainer


class WLoopPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WLoopPage")
        self.wloop_container = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("WLoop", self)
        layout.addWidget(title)

        self.wloop_container = ComboWLoopContainer(self)
        layout.addWidget(self.wloop_container, stretch=1)
