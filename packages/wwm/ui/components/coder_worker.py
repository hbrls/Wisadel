"""通用的 QThread KiloCode 调用封装"""

from PySide6.QtCore import QThread, Signal
from coders.kilocode import KiloCode


class CoderWorker(QThread):
    """通用的 QThread 封装 KiloCode 调用，解决 UI 线程阻塞问题。"""

    error = Signal(str)

    def __init__(self, cwd: str, prompt: str, parent=None):
        super().__init__(parent)
        self._cwd = cwd
        self._prompt = prompt

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
