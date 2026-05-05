"""Runbook WLoop Container UI 组件"""

import os
from string import Template

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import PrimaryPushButton, PushButton, ProgressRing, BodyLabel, FluentIcon as FIF

from ui.styles import COLORS, SPACING

from runbooks.wloop import WLoop
from ui.components.directory_selector import DirectorySelector
from ui.components.file_selector import FileSelector
from ui.components.coder_worker import CoderWorker


class WLoopSoloEpisode(QWidget):
    """WLoop 专用的 FileSelector + ProgressRing 纵向排列执行单元
    
    状态展示使用 ProgressRing，基于 Worker elapsed_changed，5 分钟 = 100%。
    """

    file_changed = Signal(str)
    run_finished = Signal()

    PROGRESS_RING_SIZE = 40
    PROGRESS_SECONDS_MAX = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_selector = FileSelector(parent=self)
        self._working_directory = ""
        self._file_value = ""
        self._prompt = Template("")
        self._worker = None
        self._sm_locked = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        layout.addWidget(self.file_selector)

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(SPACING["sm"])

        self._run_button = PushButton("Solo", self)
        self._run_button.setFixedSize(100, 33)
        status_layout.addWidget(self._run_button)

        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        status_layout.addSpacerItem(spacer)

        ring_container = QWidget(self)
        ring_container.setFixedSize(self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)
        ring_container.setStyleSheet("background: transparent; border: none;")

        self._progress_ring = ProgressRing(ring_container)
        self._progress_ring.setFixedSize(self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)
        self._progress_ring.setValue(0)

        self._progress_label = BodyLabel("0s", ring_container)
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setGeometry(0, 0, self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)

        status_layout.addWidget(ring_container)

        layout.addLayout(status_layout)

    def _connect_signals(self):
        self.file_selector.file_changed.connect(self.file_changed.emit)
        self._run_button.clicked.connect(self._on_run_requested)

    def set_working_directory(self, directory: str):
        self._working_directory = directory

    def set_file_value(self, value: str):
        self._file_value = value
        self.file_selector.set_value(value)
        self.file_selector.set_base_directory(self._working_directory)

    def set_prompt(self, prompt: Template):
        self._prompt = prompt

    def get_prompt(self) -> str:
        return self._prompt.substitute(filename=self._file_value)

    def get_cwd(self) -> str:
        return self._working_directory

    def set_sm_locked(self, locked: bool):
        self._sm_locked = locked
        if locked:
            self._run_button.setEnabled(False)
        else:
            self._run_button.setEnabled(self._worker is None)

    def _on_run_requested(self):
        if self._sm_locked:
            return
        prompt = self._prompt.substitute(filename=self._file_value)
        cwd = self._working_directory
        print(f"[WLoopSoloEpisode] run: cwd={cwd}, prompt={prompt}")

        self._run_button.setEnabled(False)
        self._progress_ring.setValue(0)
        self._progress_label.setText("0s")

        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.elapsed_changed.connect(self._on_elapsed_changed)
        self._worker.start()

    def _on_worker_finished(self):
        self._worker = None
        if not self._sm_locked:
            self._run_button.setEnabled(True)
        self.run_finished.emit()

    def _on_worker_error(self, message: str):
        print(f"[WLoopSoloEpisode] error: {message}")
        self._worker = None
        if not self._sm_locked:
            self._run_button.setEnabled(True)
        self.run_finished.emit()

    def _on_elapsed_changed(self, seconds: int):
        percent = min(int(seconds / self.PROGRESS_SECONDS_MAX * 100), 100)
        self._progress_ring.setValue(percent)
        self._progress_label.setText(f"{seconds}s")

    def set_button_enabled(self, enabled: bool):
        if self._sm_locked:
            self._run_button.setEnabled(False)
        else:
            self._run_button.setEnabled(enabled)


class RunbookWLoopContainer(QWidget):
    """Runbook WLoop Container 组件

    Container 持有：
    - self.wloop = WLoop()（Domain 数据）
    - self._episodes = []（多个 Episode）
    - self._run_button（Container 的 Run Button）
    - self._worker（CoderWorker）

    Container 的 Run Button 控制循环执行。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wloop = WLoop()
        self._syncing = False
        self._directory_selector = None
        self._episodes = []
        self._run_button = None
        self._worker = None
        self._setup_ui()
        self._connect_signals()
        if not self.wloop.working_directory:
            self.wloop.working_directory = os.path.expanduser("~")
        self._sync_ui()

    def _get_relative_path(self, absolute_path: str) -> str:
        if self.wloop.working_directory and absolute_path.startswith(self.wloop.working_directory):
            return absolute_path[len(self.wloop.working_directory):].lstrip("/\\")
        return absolute_path

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._directory_selector = DirectorySelector(
            parent=self,
            button_text="选择目录",
            placeholder_text="选择工作目录",
        )
        layout.addWidget(self._directory_selector)

        for episode_data in self.wloop.episodes:
            episode = WLoopSoloEpisode(parent=self)
            layout.addWidget(episode)
            self._episodes.append(episode)

        self._run_button = PrimaryPushButton(FIF.PLAY, "")
        self._run_button.setStyleSheet(f"PrimaryPushButton {{ background-color: {COLORS['fluent_primary']}; border: none; border-radius: 4px; }}" )
        layout.addWidget(self._run_button)

    def _connect_signals(self):
        self._directory_selector.directory_changed.connect(self._on_directory_changed)
        for i, episode in enumerate(self._episodes):
            episode.file_changed.connect(lambda path, idx=i: self._on_file_changed(idx, path))
        self._run_button.clicked.connect(self._on_run_requested)

    def _sync_ui(self):
        self._syncing = True

        self._directory_selector.set_value(self.wloop.working_directory)

        for i, episode in enumerate(self._episodes):
            episode_data = self.wloop.episodes[i]
            episode.set_working_directory(self.wloop.working_directory)
            episode.set_file_value(episode_data.filename)
            episode.set_prompt(episode_data.prompt)

        self._syncing = False

    def _on_directory_changed(self, path: str):
        if self._syncing:
            return
        self.wloop.working_directory = path
        self._sync_ui()
        print(f"[WLoopContainer] working_directory={self.wloop.working_directory}")

    def _on_file_changed(self, episode_index: int, relative_path: str):
        if self._syncing:
            return
        self.wloop.episodes[episode_index].filename = relative_path
        self._sync_ui()
        print(f"[WLoopContainer] episode[{episode_index}].filename={relative_path}")

    def _on_run_requested(self):
        """Container 的 Run Button 点击：查询状态机决定是否执行"""
        action = self.wloop.state_machine.next_action()
        if action in ("start_run", "continue_run"):
            self._start_worker()
            print(f"[WLoopContainer] Run started (action={action}, count={self.wloop.state_machine.current_count})")
        else:
            print("[WLoopContainer] Stop - loop limit reached")

    def _start_worker(self):
        episode = self._episodes[0]
        prompt = episode.get_prompt()
        cwd = episode.get_cwd()

        for ep in self._episodes:
            ep.set_sm_locked(True)

        self._run_button.setEnabled(False)
        for ep in self._episodes:
            ep.set_button_enabled(False)

        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_worker_finished(self):
        self._worker = None
        action = self.wloop.state_machine.next_action()
        if action == "continue_run":
            self._start_worker()
            print(f"[WLoopContainer] Run completed, continuing... (count={self.wloop.state_machine.current_count})")
        else:
            self._enable_buttons()
            print(f"[WLoopContainer] Run completed, all loops finished (total={self.wloop.state_machine.current_count})")
        self._sync_ui()

    def _on_worker_error(self, message: str):
        print(f"[WLoopContainer] error: {message}")
        self._worker = None
        self._enable_buttons()
        print(f"[WLoopContainer] Run finished with error (total={self.wloop.state_machine.current_count})")

    def _enable_buttons(self):
        self._run_button.setEnabled(True)
        self.wloop.state_machine.reset()
        for ep in self._episodes:
            ep.set_sm_locked(False)
            ep.set_button_enabled(True)
