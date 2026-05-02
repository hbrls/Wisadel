"""
WWM Main Entry Point

启动 WWM 桌面客户端主程序。
"""

import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui import styles

# from agents.providers.minimax_provider import MinimaxProvider
# from agents.providers.bailian_provider import BailianProvider
# from agents.providers.volcengine_provider import VolcengineProvider
from coders.kilocode import KiloCode
from coders.claudecode import ClaudeCode


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("WWM")
    app.setOrganizationName("Wishadel")

    # Apply custom stylesheet
    styles.apply_stylesheet(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Verify modules are installed correctly
    # MinimaxProvider.probe()
    # BailianProvider.probe()
    # VolcengineProvider.probe()
    # KiloCode.probe()
    # ClaudeCode.probe()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
