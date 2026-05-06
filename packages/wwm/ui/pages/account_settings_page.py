from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import SubtitleLabel

from ui.styles import SPACING


class AccountPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AccountPage")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("Account", self)
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        title = SubtitleLabel("Settings", self)
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
