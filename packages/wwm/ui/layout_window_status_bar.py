"""
Layout Window Status Bar for WWM Desktop Client

半透明状态栏组件。
"""

from PySide6.QtWidgets import QStatusBar


class LayoutWindowStatusBar(QStatusBar):
    """半透明状态栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QStatusBar { background: rgba(245, 245, 245, 26); }")
        self.setAutoFillBackground(False)
        self.showMessage("Ready")
