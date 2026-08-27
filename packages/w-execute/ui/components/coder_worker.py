"""KiloCode 调用封装"""

import time
from PySide6.QtCore import QThread, Signal, QTimer
from coders.kilocode import KiloCode


class CoderWorker(QThread):
    """通用的 QThread 封装 KiloCode 调用，解决 UI 线程阻塞问题。
    
    QTimer 在主线程运行，通过信号触发 start/stop。
    """

    error = Signal(str)
    elapsed_changed = Signal(int)
    started = Signal()
    finished = Signal()

    def __init__(self, cwd: str, prompt: str, parent=None):
        super().__init__(parent)
        self._cwd = cwd
        self._prompt = prompt
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)
        self._start_time = None
        self.finished.connect(self._stop_timer)

    def _on_elapsed_tick(self):
        if self._start_time:
            elapsed = int(time.time() - self._start_time)
            self.elapsed_changed.emit(elapsed)

    def _stop_timer(self):
        self._elapsed_timer.stop()

    def start(self):
        super().start()
        self._start_time = time.time()
        self._elapsed_timer.start()
        self.started.emit()

    def run(self):
        try:
            coder = KiloCode()
            result = coder.run_prompt(self._cwd, self._prompt)
            if result is None:
                self.error.emit("命令执行失败")
        except FileNotFoundError as e:
            self.error.emit(f"工作目录不存在: {e}")
        except PermissionError as e:
            self.error.emit(f"权限不足: {e}")
        except Exception as e:
            self.error.emit(f"执行异常: {e}")
