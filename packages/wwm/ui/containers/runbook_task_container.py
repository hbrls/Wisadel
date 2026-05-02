"""Runbook Task Container UI 组件"""

import os
from string import Template

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from runbooks.task import Task
from ui.components.directory_selector_builder import DirectorySelectorBuilder
from ui.components.file_selector_builder import FileSelectorBuilder
from ui.components.solo_runner_builder import SoloRunnerBuilder
from ui.components.coder_worker import CoderWorker


class SoloEpisode(QWidget):
    """FileSelector + SoloRunner 横向排列的单次执行单元

    Episode 的 Run Button 受 dual-gate 控制：_sm_locked 和 _worker 状态。
    Container 的状态机锁定时，Episode 的按钮被禁用；
    解锁后根据 worker 状态恢复按钮。
    """

    run_finished = Signal()
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
        """连接 SoloRunner 和 FileSelector 信号"""
        self.solo_runner.run_requested.connect(self._on_run_requested)
        self.file_selector.file_changed.connect(self.file_changed.emit)

    def set_working_directory(self, directory: str):
        """设置工作目录"""
        self._working_directory = directory
        self.solo_runner.set_working_directory(directory)

    def set_file_value(self, value: str):
        """设置关联的文件值（相对路径），同步 UI"""
        self._file_value = value
        self.file_selector.set_value(value)
        self.file_selector.set_base_directory(self._working_directory)

    def set_prompt(self, prompt: Template):
        """设置 prompt 模板"""
        self._prompt = prompt

    def get_prompt(self) -> str:
        """获取渲染后的 prompt"""
        return self._prompt.substitute(filename=self._file_value)

    def get_cwd(self) -> str:
        """获取工作目录"""
        return self._working_directory

    def set_sm_locked(self, locked: bool):
        """设置状态机锁定：locked 时禁用按钮，unlocked 时根据 worker 状态恢复"""
        self._sm_locked = locked
        if locked:
            self.solo_runner.set_button_enabled(False)
        else:
            self.solo_runner.set_button_enabled(self._worker is None)

    def set_button_enabled(self, enabled: bool):
        """设置按钮启用状态，受 _sm_locked 约束"""
        if self._sm_locked:
            self.solo_runner.set_button_enabled(False)
        else:
            self.solo_runner.set_button_enabled(enabled)

    def _on_run_requested(self):
        """执行按钮事件处理：创建 CoderWorker 并启动"""
        if self._sm_locked:
            return
        prompt = self._prompt.substitute(filename=self._file_value)
        cwd = self._working_directory
        print(f"[SoloEpisode] run: cwd={cwd}, prompt={prompt}")

        self.solo_runner.set_button_enabled(False)

        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_worker_finished(self):
        """CoderWorker 成功完成"""
        self.solo_runner.set_status(0, "Done")
        self._worker = None
        if not self._sm_locked:
            self.solo_runner.set_button_enabled(True)
        self.run_finished.emit()

    def _on_worker_error(self, message: str):
        """CoderWorker 执行出错"""
        print(f"[SoloEpisode] error: {message}")
        self._worker = None
        if not self._sm_locked:
            self.solo_runner.set_button_enabled(True)
        self.run_finished.emit()


class RunbookTaskContainer(QWidget):
    """Runbook Task Container 组件（UI 层）

    状态控制器：持有 Task 作为单一状态源，通过 Signal 接收子组件事件，
    通过 _sync_ui() 统一推送状态到所有子组件。

    Container 的 Run Button 控制顺序执行（explore → execute → evaluate）。
    """

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._syncing = False
        self._directory_selector = None
        self._solo_episodes = {}
        self._episode_list = []
        self._run_button = None
        self._worker = None
        self._setup_ui()
        self._connect_signals()
        if not self.task.working_directory:
            self.task.working_directory = os.path.expanduser("~")
        self._sync_ui()

    def _get_relative_path(self, absolute_path: str) -> str:
        if self.task.working_directory and absolute_path.startswith(self.task.working_directory):
            return absolute_path[len(self.task.working_directory):].lstrip("/\\")
        return absolute_path

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._directory_selector = DirectorySelectorBuilder(parent=self)
        dir_layout = self._directory_selector.build(
            parent=self,
            button_text="选择目录",
            placeholder_text="选择工作目录",
        )
        layout.addLayout(dir_layout)

        for episode in self.task.episodes:
            solo = SoloEpisode(parent=self)
            layout.addWidget(solo)
            self._solo_episodes[episode.id] = solo
            self._episode_list.append(solo)

        self._run_button = QPushButton("Run")
        self._run_button.setFixedSize(100, 36)
        layout.addWidget(self._run_button)

    def _connect_signals(self):
        self._directory_selector.directory_changed.connect(self._on_directory_changed)

        for i, episode in enumerate(self.task.episodes):
            solo = self._solo_episodes[episode.id]
            solo.file_changed.connect(
                lambda path, idx=i: self._on_file_changed(idx, path)
            )
            solo.run_finished.connect(self._on_run_finished)

        self._run_button.clicked.connect(self._on_run_requested)

    def _sync_ui(self):
        self._syncing = True

        self._directory_selector.set_value(self.task.working_directory)

        for episode in self.task.episodes:
            solo = self._solo_episodes[episode.id]
            solo.set_working_directory(self.task.working_directory)
            solo.set_file_value(episode.filename)
            solo.set_prompt(episode.prompt)

        self._syncing = False

    def _on_directory_changed(self, path: str):
        if self._syncing:
            return
        self.task.working_directory = path
        self._sync_ui()
        print(f"[RunbookTaskContainer] working_directory={self.task.working_directory}")

    def _on_file_changed(self, episode_index: int, absolute_path: str):
        if self._syncing:
            return
        relative = self._get_relative_path(absolute_path)
        self.task.episodes[episode_index].filename = relative
        self._sync_ui()
        print(f"[RunbookTaskContainer] episode[{episode_index}].filename={relative}")

    def _on_run_requested(self):
        """Container 的 Run Button 点击：查询状态机决定是否执行"""
        action = self.task.state_machine.next_action()
        if action in ("start_run", "continue_run"):
            self._start_worker()
            print(f"[RunbookTaskContainer] Run started (action={action}, phase={self.task.state_machine.current_phase})")
        else:
            print("[RunbookTaskContainer] Stop - all episodes completed")

    def _start_worker(self):
        """创建 Worker 并启动当前 episode"""
        episode_index = self.task.state_machine.get_current_episode_index()
        episode = self._episode_list[episode_index]
        prompt = episode.get_prompt()
        cwd = episode.get_cwd()

        for ep in self._episode_list:
            ep.set_sm_locked(True)

        self._run_button.setEnabled(False)
        for ep in self._episode_list:
            ep.set_button_enabled(False)

        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_worker_finished(self):
        """Worker 成功完成：查询状态机决定是否继续执行下一个 episode"""
        self._worker = None
        action = self.task.state_machine.next_action()
        if action == "continue_run":
            self._start_worker()
            print(f"[RunbookTaskContainer] Run completed, continuing... (phase={self.task.state_machine.current_phase})")
        else:
            self._enable_buttons()
            print(f"[RunbookTaskContainer] Run completed, all episodes finished (phase={self.task.state_machine.current_phase})")
        self._sync_ui()

    def _on_worker_error(self, message: str):
        """Worker 执行出错"""
        print(f"[RunbookTaskContainer] error: {message}")
        self._worker = None
        self._enable_buttons()
        print(f"[RunbookTaskContainer] Run finished with error (phase={self.task.state_machine.current_phase})")

    def _enable_buttons(self):
        """重新启用所有按钮并重置状态机"""
        self._run_button.setEnabled(True)
        self.task.state_machine.reset()
        for ep in self._episode_list:
            ep.set_sm_locked(False)
            ep.set_button_enabled(True)

    def _on_run_finished(self):
        print("[RunbookTaskContainer] Run finished")
        self._sync_ui()
