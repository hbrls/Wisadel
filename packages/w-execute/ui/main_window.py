from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget
from qfluentwidgets import (
    FluentIcon as FIF,
    InfoBadge,
    InfoBadgePosition,
    NavigationInterface,
    NavigationItemPosition,
)

from ui.pages.wloop_page import WLoopRunPage


class MainWindow(QMainWindow):
    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._run_badges = {}
        self._setup_navigation()
        self._setup_window()
        self._setup_pages()
        self._setup_connections()

    def _setup_navigation(self):
        self.navigationInterface = NavigationInterface(
            self,
            showMenuButton=False,
            showReturnButton=False,
        )
        self.navigationInterface.setMinimumExpandWidth(self.maximumWidth() + 1)

        self.stackedWidget = QStackedWidget(self)
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.navigationInterface)
        layout.addWidget(self.stackedWidget, stretch=1)
        self.setCentralWidget(central_widget)

    def _setup_window(self):
        self.setWindowTitle("W-Execute")
        window_flags = self.windowFlags()
        window_flags &= ~Qt.WindowMaximizeButtonHint
        window_flags &= ~Qt.WindowFullscreenButtonHint
        self.setWindowFlags(window_flags)
        self.setFixedSize(720, 320)

    def _setup_pages(self):
        self.run_pages = []
        for run_number in range(1, 4):
            run_page = WLoopRunPage(
                run_id=f"run-{run_number}",
                object_name=f"Run{run_number}Page",
                parent=self,
            )
            self.addSubInterface(
                run_page,
                FIF.PASTE,
                f"Run {run_number}",
                position=NavigationItemPosition.TOP,
            )
            self.run_pages.append(run_page)
            run_page.run_container.run_state_changed.connect(
                lambda is_running, page=run_page: self._update_run_badge(page, is_running)
            )

        self.switchTo(self.run_pages[0])

    def _setup_connections(self):
        self.window_closing.connect(self._on_closing)

    def addSubInterface(self, interface, icon, text, position=NavigationItemPosition.TOP):
        """Add a page to the native-title-bar window layout."""
        self.stackedWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text,
        )

    def switchTo(self, interface):
        self.stackedWidget.setCurrentWidget(interface)
        self.navigationInterface.setCurrentItem(interface.objectName())

    @Slot()
    def _on_closing(self):
        self.close()

    def _update_run_badge(self, run_page: WLoopRunPage, is_running: bool):
        nav_widget = self.navigationInterface.widget(run_page.objectName())
        if nav_widget is None:
            return

        badge = self._run_badges.get(run_page.run_id)
        if not is_running:
            if badge:
                badge.hide()
            return

        if badge:
            badge.setText("1")
            badge.show()
            return

        self._run_badges[run_page.run_id] = InfoBadge.success(
            "1",
            self.navigationInterface.panel,
            nav_widget,
            InfoBadgePosition.NAVIGATION_ITEM,
        )
