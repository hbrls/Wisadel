"""PySide6 窗口 - 主窗口"""

import os
import threading
from string import Template

from loguru import logger
from coders import probe
import coders
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QApplication,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from _coders import run_command, run_prompt
from run_worker import RunWorker
from prompt_worker import PromptWorker
from .components import DirectorySelectorBuilder, FileSelectorBuilder, TrioRunnerBuilder, SoloRunnerBuilder
from .views.breakdown_phase import BreakdownPhaseView
from .styles import MAIN_STYLESHEET


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.run_worker = None
        self.prompt_worker = None

        # 工作目录（默认为用户主目录）
        self.working_directory = os.path.expanduser("~")

        # 窗口基本配置
        self.setWindowTitle("Dashboard")
        self.setFixedSize(960, 600)

        # 居中显示
        self.move(
            QApplication.primaryScreen().geometry().center()
            - self.frameGeometry().center()
        )

        # 设置主部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局（横排）
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建左侧 Tab 栏
        self._setup_tab_bar(main_layout)

        # 创建右侧内容区（使用 QStackedWidget）
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # Tab 1: Breakdown Phase 视图
        self.breakdown_phase_view = BreakdownPhaseView()
        self.breakdown_phase_view.set_working_directory(self.working_directory)
        self.stacked_widget.addWidget(self.breakdown_phase_view)

        # Tab 2: 第二行占位内容
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(20, 48, 20, 20)
        
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(8)
        
        btn2_1 = QPushButton("占位按钮 2-1")
        btn2_1.setEnabled(False)
        btn2_1.setFixedWidth(100)
        row2_layout.addWidget(btn2_1)
        
        text2 = QLineEdit("示例行 2 - 待实现")
        text2.setReadOnly(True)
        text2.setEnabled(False)
        text2.setFixedHeight(30)
        row2_layout.addWidget(text2)
        
        spacer2 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        row2_layout.addSpacerItem(spacer2)
        
        btn2_2 = QPushButton("占位")
        btn2_2.setEnabled(False)
        btn2_2.setFixedWidth(80)
        row2_layout.addWidget(btn2_2)
        
        tab2_layout.addLayout(row2_layout)
        tab2_layout.addStretch()
        self.stacked_widget.addWidget(tab2_widget)

        # Tab 3: 第三行占位内容
        tab3_widget = QWidget()
        tab3_layout = QVBoxLayout(tab3_widget)
        tab3_layout.setContentsMargins(20, 48, 20, 20)
        
        row3_layout = QHBoxLayout()
        row3_layout.setContentsMargins(0, 0, 0, 0)
        row3_layout.setSpacing(8)
        
        btn3_1 = QPushButton("占位按钮 3-1")
        btn3_1.setEnabled(False)
        btn3_1.setFixedWidth(100)
        row3_layout.addWidget(btn3_1)
        
        text3 = QLineEdit("示例行 3 - 待实现")
        text3.setReadOnly(True)
        text3.setEnabled(False)
        text3.setFixedHeight(30)
        row3_layout.addWidget(text3)
        
        spacer3 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        row3_layout.addSpacerItem(spacer3)
        
        btn3_2 = QPushButton("占位")
        btn3_2.setEnabled(False)
        btn3_2.setFixedWidth(80)
        row3_layout.addWidget(btn3_2)
        
        tab3_layout.addLayout(row3_layout)
        tab3_layout.addStretch()
        self.stacked_widget.addWidget(tab3_widget)

        # 默认显示 Tab 1
        self.stacked_widget.setCurrentIndex(0)

        # 应用样式
        self._apply_styles()

    def _setup_tab_bar(self, main_layout: QHBoxLayout):
        """创建左侧竖排 Tab 栏"""
        tab_bar_widget = QWidget()
        tab_bar_widget.setFixedWidth(150)
        tab_bar_layout = QVBoxLayout(tab_bar_widget)
        tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        tab_bar_layout.setSpacing(0)

        # Tab 1 按钮
        self.tab1_button = QPushButton("Breakdown Phase")
        self.tab1_button.setFixedHeight(50)
        self.tab1_button.clicked.connect(lambda: self._on_tab_clicked(0))
        self.tab1_button.setProperty("class", "tab-active")
        tab_bar_layout.addWidget(self.tab1_button)

        # Tab 2 按钮
        self.tab2_button = QPushButton("Tab 2")
        self.tab2_button.setFixedHeight(50)
        self.tab2_button.clicked.connect(lambda: self._on_tab_clicked(1))
        self.tab2_button.setProperty("class", "tab")
        tab_bar_layout.addWidget(self.tab2_button)

        # Tab 3 按钮
        self.tab3_button = QPushButton("Tab 3")
        self.tab3_button.setFixedHeight(50)
        self.tab3_button.clicked.connect(lambda: self._on_tab_clicked(2))
        self.tab3_button.setProperty("class", "tab")
        tab_bar_layout.addWidget(self.tab3_button)

        # 弹性空间
        tab_bar_layout.addStretch()

        main_layout.addWidget(tab_bar_widget)

    def _on_tab_clicked(self, index: int):
        """Tab 按钮点击事件处理"""
        # 切换内容
        self.stacked_widget.setCurrentIndex(index)
        
        # 更新所有 Tab 按钮的样式
        self.tab1_button.setProperty("class", "tab-active" if index == 0 else "tab")
        self.tab2_button.setProperty("class", "tab-active" if index == 1 else "tab")
        self.tab3_button.setProperty("class", "tab-active" if index == 2 else "tab")
        
        # 刷新样式
        self.tab1_button.style().unpolish(self.tab1_button)
        self.tab1_button.style().polish(self.tab1_button)
        self.tab2_button.style().unpolish(self.tab2_button)
        self.tab2_button.style().polish(self.tab2_button)
        self.tab3_button.style().unpolish(self.tab3_button)
        self.tab3_button.style().polish(self.tab3_button)

    def _on_directory_selected(self, selected_dir: str):
        """目录选择回调"""
        self.working_directory = selected_dir
        self.breakdown_phase_view.set_working_directory(selected_dir)
        logger.info(f"工作目录已更新: {selected_dir}")

    def _on_prepare_button_clicked(self):
        """预备按钮点击事件处理"""
        if self.run_worker and self.run_worker.isRunning():
            return

        logger.info("预备按钮被点击")
        logger.info(f"工作目录: {self.working_directory}")
        self.breakdown_phase_view.prepare_button.setEnabled(False)
        self.breakdown_phase_view.start_button.setEnabled(False)

        # 重置状态显示
        self.breakdown_phase_view.reset_status_display()

        command = """
        kilocode run --model dashscope/glm-5 "阅读 TASK.md，根据 # Instruction 更新 # Current Task。"
        """.strip()

        self.run_worker = RunWorker(command, cwd=self.working_directory)
        self.run_worker.finished.connect(self._on_run_finished)
        self.run_worker.error.connect(self._on_run_error)
        self.run_worker.status_update.connect(self._on_status_update)
        self.run_worker.start()

    def _on_start_button_clicked(self):
        """开始按钮点击事件处理"""
        if self.run_worker and self.run_worker.isRunning():
            return

        logger.info("开始按钮被点击")
        logger.info(f"工作目录: {self.working_directory}")
        self.breakdown_phase_view.prepare_button.setEnabled(False)
        self.breakdown_phase_view.start_button.setEnabled(False)

        # 重置状态显示
        self.breakdown_phase_view.reset_status_display()

        command = """
        kilocode run --model dashscope/glm-5 "阅读 TASK.md，执行 # Current Task。"
        """.strip()

        self.run_worker = RunWorker(command, cwd=self.working_directory)
        self.run_worker.finished.connect(self._on_run_finished)
        self.run_worker.error.connect(self._on_run_error)
        self.run_worker.status_update.connect(self._on_status_update)
        self.run_worker.start()

    def _on_prompt_finished(self):
        """Prompt 执行完成回调"""
        self._enable_action_buttons()
        self.prompt_worker = None
        logger.info("Prompt 执行完成")

    def _on_prompt_error(self, error_msg: str):
        """Prompt 执行失败回调"""
        self._enable_action_buttons()
        self.prompt_worker = None
        logger.error(f"Prompt 执行失败: {error_msg}")

    def _run_prompt_async(self, prompt: str):
        """异步执行 prompt"""
        if self.prompt_worker and self.prompt_worker.isRunning():
            return

        self._disable_action_buttons()
        self.prompt_worker = PromptWorker(prompt, cwd=self.working_directory)
        self.prompt_worker.finished.connect(self._on_prompt_finished)
        self.prompt_worker.error.connect(self._on_prompt_error)
        self.prompt_worker.start()

    def _on_run_finished(self):
        """命令执行完成回调"""
        self.breakdown_phase_view.prepare_button.setEnabled(True)
        self.breakdown_phase_view.start_button.setEnabled(True)
        self.run_worker = None
        # 清空状态显示
        self.breakdown_phase_view.reset_status_display()
        logger.info("命令执行完成")

    def _on_run_error(self, error_msg: str):
        """命令执行失败回调"""
        self.breakdown_phase_view.prepare_button.setEnabled(True)
        self.breakdown_phase_view.start_button.setEnabled(True)
        self.run_worker = None
        # 清空状态显示
        self.breakdown_phase_view.reset_status_display()
        logger.error(f"命令执行失败: {error_msg}")

    def _disable_runner_buttons(self):
        """禁用所有 Runner 按钮"""
        self.breakdown_phase_view._disable_runner_buttons()

    def _enable_runner_buttons(self):
        """启用所有 Runner 按钮"""
        self.breakdown_phase_view._enable_runner_buttons()

    def _on_status_update(self, pid: int, elapsed_seconds: int):
        """状态更新回调 - 更新 PID 和运行时间显示

        Args:
            pid: 进程 ID
            elapsed_seconds: 已运行时间（秒）
        """
        self.breakdown_phase_view.update_status_display(pid, elapsed_seconds)

    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet(MAIN_STYLESHEET)

    def show(self):
        """显示窗口"""
        super().show()
        self.activateWindow()

    def hide(self):
        """隐藏窗口"""
        super().hide()

    def closeEvent(self, event):
        """点击关闭按钮时隐藏到托盘，不退出程序"""
        self.hide()
        event.ignore()
