"""Combo ALoop Container UI 组件"""

from string import Template

from loguru import logger
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import PrimaryPushButton, PushButton, ProgressRing, BodyLabel, FluentIcon as FIF, CardWidget

from ui.styles import SPACING

from combos.aloop import ALoop
from ui.components.working_dir_selector import WorkingDirSelector
from ui.components.file_selector import FileSelector
from ui.components.directory_selector import DirectorySelector
from ui.components.coder_worker import CoderWorker
from ui.components.checker_worker import CheckerWorker
from ui.components.combo_states import ComboStates


class ALoopSoloEpisode(CardWidget):
    """ALoop 专用的 FileSelector + SoloRunner 横向排列执行单元

    持有唯一的执行真源：Worker、计时、ProgressRing。
    Solo 按钮和外部 Play 都通过 start_run() 触发同一条执行链。
    """

    value_changed = Signal(str)
    run_finished = Signal(str)

    PROGRESS_RING_SIZE = 40
    PROGRESS_SECONDS_MAX = 300

    def __init__(self, episode_id: str, prompt: Template, is_dir: bool = False, parent=None):
        super().__init__(parent)
        self.episode_id = episode_id
        self._prompt = prompt
        self._is_dir = is_dir
        if is_dir:
            self._selector = DirectorySelector(parent=self)
        else:
            self._selector = FileSelector(parent=self)
        self._working_directory = ""
        self._file_value = ""
        self._worker = None
        self._sm_locked = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])

        layout.addWidget(self._selector, stretch=1)

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
        self._selector.value_changed.connect(self._on_selector_value_changed)
        self._run_button.clicked.connect(self._on_solo_clicked)

    def set_working_directory(self, directory: str):
        self._working_directory = directory
        self._selector.set_base_directory(directory)

    def set_file_value(self, value: str):
        if self._is_dir and not value.endswith("/"):
            value += "/"
        self._file_value = value
        self._selector.set_value(value)

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

    def is_running(self) -> bool:
        return self._worker is not None

    def start_run(self):
        if self._worker is not None:
            return
        prompt = self._prompt.substitute(filename=self._file_value)
        cwd = self._working_directory
        logger.info(f"[ALoopSoloEpisode] run: cwd={cwd}, prompt={prompt}")

        self._run_button.setEnabled(False)
        self._progress_ring.setValue(0)
        self._progress_label.setText("0s")

        if prompt.startswith("CHECK_"):
            self._worker = CheckerWorker(cwd=cwd, prompt=prompt, parent=self)
        else:
            self._worker = CoderWorker(cwd=cwd, prompt=prompt, parent=self)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.elapsed_changed.connect(self._on_elapsed_changed)
        self._worker.start()

    def _on_worker_thread_finished(self, result: str = None):
        self._worker = None
        self._progress_ring.setValue(0)
        self._progress_label.setText("0s")
        if not self._sm_locked:
            self._run_button.setEnabled(True)
        self.run_finished.emit(result or "PASS")

    def _on_worker_error(self, message: str):
        logger.error(f"[ALoopSoloEpisode] error: {message}")

    def _on_elapsed_changed(self, seconds: int):
        percent = min(int(seconds / self.PROGRESS_SECONDS_MAX * 100), 100)
        self._progress_ring.setValue(percent)
        self._progress_label.setText(f"{seconds}s")

    def _on_solo_clicked(self):
        if self._sm_locked:
            return
        self.start_run()

    def _on_selector_value_changed(self, path: str):
        if self._is_dir and not path.endswith("/"):
            path += "/"
        self._file_value = path
        self.value_changed.emit(path)


class ComboALoopContainer(QWidget):
    """Combo ALoop Container 组件

    Container 只负责渲染和执行指令：
    - 渲染：foreach ep in Model.episodes, if ep.component == "ALoopSoloEpisode", render ALoopSoloEpisode
    - 执行：Model.next() 返回指令，Container 执行

    状态机控制！Container 不决策，只执行指令。
    """

    run_state_changed = Signal(bool)

    def __init__(self, run_id: str = "", parent=None):
        super().__init__(parent)
        self.run_id = run_id
        self.aloop = ALoop()
        self._play_active = False
        self._cwd_selector = None
        self._episodes = []
        self._episode_map = {}
        self._run_button = None
        self._state_history = None
        self._setup_ui()
        self._connect_signals()
        self._sync_ui()
        self._state_history.append(self.aloop.state)

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        content_widget = QWidget(self)
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, SPACING["md"], 0, 0)
        content_layout.setSpacing(SPACING["md"])

        left_panel = QWidget(content_widget)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._cwd_selector = WorkingDirSelector(
            parent=self,
            button_text="选择目录",
            placeholder_text="选择工作目录",
        )

        left_layout.addWidget(self._cwd_selector)

        for ep in self.aloop.episodes:
            if ep.component == "ALoopSoloEpisode":
                episode_ui = ALoopSoloEpisode(episode_id=ep.id, prompt=ep.prompt, is_dir=ep.filename.endswith("/"), parent=self)
                left_layout.addWidget(episode_ui)
                self._episodes.append(episode_ui)
                self._episode_map[ep.id] = episode_ui

        self._run_button = PrimaryPushButton(FIF.PLAY, "", self)
        self._run_button.setFixedHeight(33)
        left_layout.addWidget(self._run_button)

        content_layout.addWidget(left_panel, stretch=3)

        separator = QFrame(content_widget)
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(separator)

        self._state_history = ComboStates(content_widget)
        content_layout.addWidget(self._state_history, stretch=1)

        outer_layout.addWidget(content_widget, stretch=1)

    def _connect_signals(self):
        self._cwd_selector.value_changed.connect(self._on_directory_changed)
        for i, episode in enumerate(self._episodes):
            episode.run_finished.connect(self._on_episode_finished)
        self._run_button.clicked.connect(self._on_play_clicked)

    def _sync_ui(self):
        cwd = self._cwd_selector.value()
        for ep in self.aloop.episodes:
            episode_ui = self._episode_map.get(ep.id)
            if episode_ui:
                if isinstance(episode_ui, ALoopSoloEpisode):
                    episode_ui.set_working_directory(cwd)
                    episode_ui.set_file_value(ep.filename)

    def is_running(self) -> bool:
        return any(ep.is_running() for ep in self._episodes)

    def _on_directory_changed(self, path: str):
        for ep in self._episodes:
            ep.set_working_directory(path)

    def _on_play_clicked(self):
        self._play_active = True
        instruction = self.aloop.next()
        self._execute_instruction(instruction)

    def _on_episode_finished(self, result: str = None):
        if not self._play_active:
            return
        instruction = self.aloop.next(result)
        self._execute_instruction(instruction)

    def _execute_instruction(self, instruction):
        if self._play_active:
            self._state_history.append(instruction)
        if instruction in self._episode_map:
            episode = self._episode_map[instruction]
            if isinstance(episode, ALoopSoloEpisode):
                for ep in self._episodes:
                    ep.set_sm_locked(True)
                self._run_button.setEnabled(False)
                episode.start_run()
                self.run_state_changed.emit(True)
        elif instruction == "FINISHED":
            self._play_active = False
            self._run_button.setEnabled(True)
            for ep in self._episodes:
                ep.set_sm_locked(False)
                ep.set_button_enabled(True)
            self.aloop.reset()
            self._state_history.append(self.aloop.state)
            self.run_state_changed.emit(False)