"""w-execute application entry point."""

import logger_config  # 触发全局日志配置

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, setThemeColor, Theme

from ui.main_window import MainWindow
from ui import styles


def asset_path(filename: str) -> Path:
    """Resolve an application asset in source and PyInstaller environments."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / "assets" / filename


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("w-execute")
    app.setOrganizationName("Wishadel")
    app.setWindowIcon(QIcon(str(asset_path("icon-128x128.png"))))

    # Apply Fluent Design theme
    setTheme(Theme.AUTO)
    setThemeColor(QColor("#0078D4"))

    # Apply custom stylesheet
    styles.apply_stylesheet(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
