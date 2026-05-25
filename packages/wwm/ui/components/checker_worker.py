import os
import re
import time
from PySide6.QtCore import QThread, Signal, QTimer

_CHECK_PATTERN = re.compile(r"^CHECK_(\w+):\s+(.+)$")


def _check_has_dir(cwd: str, arg: str) -> str:
    full_path = os.path.normpath(os.path.join(cwd, arg))
    return "YES" if os.path.isdir(full_path) else "NO"


_CHECK_HANDLERS = {
    "HAS_DIR": _check_has_dir,
}


class CheckerWorker(QThread):
    error = Signal(str)
    elapsed_changed = Signal(int)
    finished = Signal(str)

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

    def run(self):
        m = _CHECK_PATTERN.match(self._prompt)
        if m:
            handler = _CHECK_HANDLERS.get(m.group(1))
            result = handler(self._cwd, m.group(2)) if handler else "PASS"
        else:
            result = "PASS"
        self.finished.emit(result)
