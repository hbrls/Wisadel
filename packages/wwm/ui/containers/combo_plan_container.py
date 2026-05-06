"""Combo Plan Container UI 组件"""

import os
from string import Template

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import PrimaryPushButton, PushButton, ProgressRing, BodyLabel, FluentIcon as FIF, CardWidget

from ui.styles import SPACING
from combos.plan import Plan
from ui.components.working_dir_selector import WorkingDirSelector
from ui.components.file_selector import FileSelector
from ui.components.coder_worker import CoderWorker


class PlanSoloEpisode(CardWidget):
    """Plan 专用的 FileSelector + SoloRunner 横向排列执行单元

    持有唯一的执行真源：Worker、计时、ProgressRing。
    Solo 按钮和外部 Play 都通过 start_run() 触发同一条执行链。
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])

        layout.addWidget(self.file_selector, stretch=1)

        solo_runner_layout = QHBoxLayout()
        solo_runner_layout.setContentsMargins(0, 0, 0, 0)
        solo_runner_layout.setSpacing(SPACING["sm"])

        ring_container = QWidget(self)
        ring_container.setFixedSize(self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)
        ring_container.setStyleSheet("background: transparent; border: none;")

        self._progress_ring = ProgressRing(ring_container)
        self._progress_ring.setFixedSize(self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)
        self._progress_ring.setValue(0)

        self._progress_label = BodyLabel("0s", ring_container)
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setGeometry(0, 0, self.PROGRESS_RING_SIZE, self.PROGRESS_RING_SIZE)

        solo_runner_layout.addWidget(ring_container)

        self._run_button = PushButton("Solo", self)
        self._run_button.setFixedSize(100, 33)
        solo_runner_layout.addWidget(self._run_button)

        layout.addLayout(solo_runner_layout)

    def _connect_signals(self):
        self.file_selector.file_changed.connect(self.file_changed.emit)
        self._run_button.clicked.connect(self._on_solo_clicked)

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

    def is_running(self) -> bool:
        return self._worker is not None

    def start_run(self):
        if self._worker is not None:
            return
        prompt = self._prompt.substitute(filename=self._file_value)
        cwd = self._working_directory
        print(f"[PlanSoloEpisode] run: cwd={cwd}, prompt={prompt}")

        self._run_button.setEnabled(False)
        self._progress_ring.setValue(0)
        self._progress_label.setText("0s")

        self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.elapsed_changed.connect(self._on_elapsed_changed)
        self._worker.start()

    def _on_solo_clicked(self):
        if self._sm_locked:
            return
        self.start_run()

    def _on_worker_error(self, message: str):
        print(f"[PlanSoloEpisode] error: {message}")

    def _on_worker_thread_finished(self):
        self._worker = None
        self._progress_ring.setValue(0)
        self._progress_label.setText("0s")
        if not self._sm_locked:
            self._run_button.setEnabled(True)
        self.run_finished.emit()

    def _on_elapsed_changed(self, seconds: int):
        percent = min(int(seconds / self.PROGRESS_SECONDS_MAX * 100), 100)
        self._progress_ring.setValue(percent)
        self._progress_label.setText(f"{seconds}s")

    def set_sm_locked(self, locked: bool):
        self._sm_locked = locked
        if locked:
            self._run_button.setEnabled(False)
        else:
            self._run_button.setEnabled(self._worker is None)

    def set_button_enabled(self, enabled: bool):
        if self._sm_locked:
            self._run_button.setEnabled(False)
        else:
            self._run_button.setEnabled(enabled)


class ComboPlanContainer(QWidget):
    """Combo Plan Container 组件

    Container 只负责编排：
    - Play 按钮触发当前 Episode 的 start_run()，不自己创建 Worker。
    - 通过 Episode 的 run_finished 信号决定是否继续下一轮。
    - 不持有 Worker / Timer / Progress 等执行态。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan = Plan()
        self._syncing = False
        self._directory_selector = None
        self._episodes = []
        self._run_button = None
        self._setup_ui()
        self._connect_signals()
        if not self.plan.working_directory:
            self.plan.working_directory = os.path.expanduser("~")
        self._sync_ui()

    def _get_relative_path(self, absolute_path: str) -> str:
        if self.plan.working_directory and absolute_path.startswith(self.plan.working_directory):
            return absolute_path[len(self.plan.working_directory):].lstrip("/\\")
        return absolute_path

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._directory_selector = WorkingDirSelector(
            parent=self,
            button_text="选择目录",
            placeholder_text="选择工作目录",
        )

        layout.addWidget(self._directory_selector)

        for episode_data in self.plan.episodes:
            episode = PlanSoloEpisode(parent=self)
            layout.addWidget(episode)
            self._episodes.append(episode)

        self._run_button = PrimaryPushButton(FIF.PLAY, "", self)
        self._run_button.setFixedHeight(33)
        layout.addWidget(self._run_button)

    def _connect_signals(self):
        self._directory_selector.directory_changed.connect(self._on_directory_changed)
        for i, episode in enumerate(self._episodes):
            episode.file_changed.connect(lambda path, idx=i: self._on_file_changed(idx, path))
            episode.run_finished.connect(self._on_episode_finished)
        self._run_button.clicked.connect(self._on_play_clicked)

    def _sync_ui(self):
        self._syncing = True

        self._directory_selector.set_value(self.plan.working_directory)

        for i, episode in enumerate(self._episodes):
            episode_data = self.plan.episodes[i]
            episode.set_working_directory(self.plan.working_directory)
            episode.set_file_value(episode_data.filename)
            episode.set_prompt(episode_data.prompt)

        self._syncing = False

    def _on_directory_changed(self, path: str):
        if self._syncing:
            return
        self.plan.working_directory = path
        self._sync_ui()
        print(f"[PlanContainer] working_directory={self.plan.working_directory}")

    def _on_file_changed(self, episode_index: int, relative_path: str):
        if self._syncing:
            return
        self.plan.episodes[episode_index].filename = relative_path
        self._sync_ui()
        print(f"[PlanContainer] episode[{episode_index}].filename={relative_path}")

    def _on_play_clicked(self):
        action = self.plan.state_machine.next_action()
        if action in ("start_run", "continue_run"):
            episode_index = self.plan.state_machine.get_current_episode_index()
            episode = self._episodes[episode_index]
            if episode.is_running():
                return
            for ep in self._episodes:
                ep.set_sm_locked(True)
            self._run_button.setEnabled(False)
            episode.start_run()
            print(f"[PlanContainer] Run started (action={action}, phase={self.plan.state_machine.current_phase})")
        else:
            print("[PlanContainer] Stop - all episodes completed")

    def _on_episode_finished(self):
        action = self.plan.state_machine.next_action()
        if action == "continue_run":
            episode_index = self.plan.state_machine.get_current_episode_index()
            episode = self._episodes[episode_index]
            episode.start_run()
            print(f"[PlanContainer] Run completed, continuing... (phase={self.plan.state_machine.current_phase})")
        else:
            self._run_button.setEnabled(True)
            self.plan.state_machine.reset()
            for ep in self._episodes:
                ep.set_sm_locked(False)
                ep.set_button_enabled(True)
            print(f"[PlanContainer] Run completed, all episodes finished (phase={self.plan.state_machine.current_phase})")
        self._sync_ui()