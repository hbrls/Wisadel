from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ListWidget


class ComboStates(QWidget):
    """状态历史展示组件
    
    显示状态机的执行步骤历史。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._list_widget = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._list_widget = ListWidget(self)
        layout.addWidget(self._list_widget)

    def append(self, state: str):
        self._list_widget.addItem(state)

    def reset(self, initial_state: str):
        self._list_widget.clear()
        self._list_widget.addItem(initial_state)