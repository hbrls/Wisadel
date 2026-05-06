from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget, QStatusBar
from qfluentwidgets import FluentWindow, FluentIcon as FIF, NavigationItemPosition, InfoBadge, InfoBadgePosition

from ui.pages.bootstrap_page import BootstrapPage
from ui.pages.task_page import TaskPage
from ui.pages.wloop_page import WLoopPage
from ui.pages.account_settings_page import AccountPage, SettingsPage


class MainWindow(FluentWindow):
    window_closing = Signal()
    _wloop_badge = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigationInterface.setReturnButtonVisible(False)
        self._setup_window()
        self._restructure_content_area()
        self._setup_pages()
        self._setup_connections()

    def _setup_window(self):
        self.setWindowTitle("维维美")
        self.setMinimumSize(900, 500)
        self.setMicaEffectEnabled(False)

    def _restructure_content_area(self):
        self.widgetLayout.removeWidget(self.stackedWidget)

        content_widget = QWidget()
        content_vbox = QVBoxLayout(content_widget)
        content_vbox.setContentsMargins(0, 0, 0, 0)
        content_vbox.setSpacing(0)

        content_vbox.addWidget(self.stackedWidget, stretch=1)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        content_vbox.addWidget(self.status_bar)

        self.widgetLayout.addWidget(content_widget)

    def _setup_pages(self):
        self.bootstrap_page = BootstrapPage(self)
        self.addSubInterface(
            self.bootstrap_page, FIF.APPLICATION, "Bootstrap",
            position=NavigationItemPosition.TOP,
        )

        self.task_page = TaskPage(self)
        self.addSubInterface(
            self.task_page, FIF.CHECKBOX, "Task",
            position=NavigationItemPosition.TOP,
        )

        self.wloop_page = WLoopPage(self)
        self.addSubInterface(
            self.wloop_page, FIF.SYNC, "WLoop",
            position=NavigationItemPosition.TOP,
        )

        self.wloop_page.wloop_container.play_started.connect(self._show_wloop_badge)
        self.wloop_page.wloop_container.play_stopped.connect(self._hide_wloop_badge)

        self.account_page = AccountPage(self)
        self.addSubInterface(
            self.account_page, FIF.PEOPLE, "Account",
            position=NavigationItemPosition.BOTTOM,
        )

        self.settings_page = SettingsPage(self)
        self.addSubInterface(
            self.settings_page, FIF.SETTING, "Settings",
            position=NavigationItemPosition.BOTTOM,
        )

        self.switchTo(self.bootstrap_page)

    def _setup_connections(self):
        self.window_closing.connect(self._on_closing)

    @Slot()
    def _on_closing(self):
        self.close()

    def update_status(self, message: str):
        self.status_bar.showMessage(message)

    def _show_wloop_badge(self):
        nav_widget = self.navigationInterface.widget("WLoopPage")
        if self._wloop_badge:
            self._wloop_badge.show()
        else:
            self._wloop_badge = InfoBadge.success(
                "1", 
                self.navigationInterface.panel,
                nav_widget, 
                InfoBadgePosition.NAVIGATION_ITEM
            )

    def _hide_wloop_badge(self):
        if self._wloop_badge:
            self._wloop_badge.hide()
