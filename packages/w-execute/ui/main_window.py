from PySide6.QtCore import Signal, Slot
from qfluentwidgets import FluentWindow, FluentIcon as FIF, NavigationItemPosition, InfoBadge, InfoBadgePosition

from ui.pages.wloop_page import WLoopRunPage


class MainWindow(FluentWindow):
    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._run_badges = {}
        self.navigationInterface.setReturnButtonVisible(False)
        self.navigationInterface.setMinimumExpandWidth(self.maximumWidth() + 1)
        self.navigationInterface.setMenuButtonVisible(False)
        self._setup_window()
        self._setup_pages()
        self._setup_connections()

    def _setup_window(self):
        self.setWindowTitle("W-Execute")
        self.setMinimumSize(800, 360)
        self.resize(800, 360)
        self.setMicaEffectEnabled(False)

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
                FIF.SYNC,
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
