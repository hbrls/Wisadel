from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.styles import SPACING
from ui.containers.combo_wloop_container import ComboWLoopContainer


class WLoopRunPage(QWidget):
    """页面级包装：一个导航页面对应一个固定的 WLoop Run。"""

    def __init__(self, run_id: str, object_name: str, parent=None):
        super().__init__(parent)
        self.run_id = run_id
        self.setObjectName(object_name)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        self.run_container = ComboWLoopContainer(run_id=self.run_id, parent=self)
        layout.addWidget(self.run_container, stretch=1)
