from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget

from ui.styles import SPACING
from ui.components.directory_selector import DirectorySelector


class WorkingDirSelector(CardWidget):

    directory_changed = Signal(str)

    def __init__(self, parent=None, button_text: str = "选择目录", placeholder_text: str = "选择工作目录"):
        super().__init__(parent)
        self._directory_selector = DirectorySelector(
            parent=self,
            button_text=button_text,
            placeholder_text=placeholder_text,
        )
        self._setup_ui()
        self._directory_selector.directory_changed.connect(self.directory_changed.emit)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(0)
        layout.addWidget(self._directory_selector)

    def set_value(self, path: str):
        self._directory_selector.set_value(path)

    def value(self) -> str:
        return self._directory_selector.value()
