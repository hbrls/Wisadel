"""Runbook WLoop Container UI 组件"""

import os
from string import Template

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from runbooks.wloop import WLoop
from ui.components.directory_selector_builder import DirectorySelectorBuilder
from ui.components.file_selector_builder import FileSelectorBuilder
from ui.components.solo_runner_builder import SoloRunnerBuilder
from ui.components.coder_worker import CoderWorker


class WLoopSoloEpisode(QWidget):
    """WLoop 专用的 FileSelector + SoloRunner 横向排列执行单元

    Episode 的 Run Button 只打印，不执行实际动作。
    实际执行由 Container 的 Run Button 控制。
    """

    file_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_selector = FileSelectorBuilder(parent=self)
        self.solo_runner = SoloRunnerBuilder(parent=self)
        self._working_directory = ""
        self._file_value = ""
        self._prompt = Template("")
        self._worker = None
        self._sm_locked = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        file_layout = self.file_selector.build(
            parent=self,
            default_value="",
            button_text="选择文件",
            placeholder_text="选择文件",
        )
        layout.addLayout(file_layout)

        runner_layout = self.solo_runner.build(
            working_directory="",
            session_ids=[],
            session_offset=0,
            prompt=Template(""),
            button_text="Run",
            default_value="--:--",
        )
        layout.addLayout(runner_layout)

    def _connect_signals(self):
        self.file_selector.file_changed.connect(self.file_changed.emit)
        self.solo_runner.run_requested.connect(self._on_run_requested)

    def set_working_directory(self, directory: str):
        self._working_directory = directory
        self.solo_runner.set_working_directory(directory)

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
            self.solo_runner.set_button_enabled(False)
        else:
            self.solo_runner.set_button_enabled(self._worker is None)

    def _on_run_requested(self):
        if self._sm_locked:
            return
        prompt = self._prompt.substitute(filename=self._file_value)
        cwd = self._working_directory
        print(f"[WLoopSoloEpisode] run: cwd={cwd}, prompt={prompt}")
        self.solo_runner.set_button_enabled(False)
        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_worker_finished(self):
        self.solo_runner.set_status(0, "Done")
        self._worker = None
        if not self._sm_locked:
            self.solo_runner.set_button_enabled(True)
        self.solo_runner.run_finished.emit()

    def _on_worker_error(self, message: str):
        print(f"[WLoopSoloEpisode] error: {message}")
        self._worker = None
        if not self._sm_locked:
            self.solo_runner.set_button_enabled(True)
        self.solo_runner.run_finished.emit()

    def set_button_enabled(self, enabled: bool):
        if self._sm_locked:
            self.solo_runner.set_button_enabled(False)
        else:
            self.solo_runner.set_button_enabled(enabled)


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

        self._directory_selector = DirectorySelectorBuilder(parent=self)
        dir_layout = self._directory_selector.build(
            parent=self,
            default_value=os.path.expanduser("~"),
            button_text="选择目录",
            placeholder_text="选择目录",
        )
        layout.addLayout(dir_layout)

        for episode_data in self.wloop.episodes:
            episode = WLoopSoloEpisode(parent=self)
            layout.addWidget(episode)
            self._episodes.append(episode)

        self._run_button = QPushButton("Run")
        self._run_button.setFixedSize(100, 36)
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

    def _on_file_changed(self, episode_index: int, absolute_path: str):
        if self._syncing:
            return
        relative = self._get_relative_path(absolute_path)
        self.wloop.episodes[episode_index].filename = relative
        self._sync_ui()
        print(f"[WLoopContainer] episode[{episode_index}].filename={relative}")

    def _on_run_requested(self):
        """Container 的 Run Button 点击：查询状态机决定是否执行"""
        action = self.wloop.state_machine.next_action()
        if action in ("start_run", "continue_run"):
            self._start_worker()
            print(f"[WLoopContainer] Run started (action={action}, count={self.wloop.state_machine.current_count})")
        else:
            print("[WLoopContainer] Stop - loop limit reached")

    def _start_worker(self):
        """创建 Worker 并启动"""
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
        """Worker 成功完成：查询状态机决定是否继续"""
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
        """Worker 执行出错"""
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