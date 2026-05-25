from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import TabWidget

from ui.styles import SPACING
from ui.containers.combo_aloop_container import ComboALoopContainer


class ALoopPage(QWidget):
    running_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ALoopPage")
        self._run_containers = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        self._tab_widget = TabWidget(self)

        for i in range(1, 4):
            run_container = ComboALoopContainer(run_id=f"run-{i}", parent=self)
            run_container.run_state_changed.connect(self._on_child_state_changed)
            self._run_containers.append(run_container)
            self._tab_widget.addTab(run_container, f"Run {i}")

        layout.addWidget(self._tab_widget, stretch=1)

    def _on_child_state_changed(self, is_running: bool):
        count = sum(1 for c in self._run_containers if c.is_running())
        self.running_count_changed.emit(count)