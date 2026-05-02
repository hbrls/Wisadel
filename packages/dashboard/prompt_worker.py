"""Prompt 执行工作线程

将 run_prompt 调用放到后台线程执行，避免阻塞 UI。
"""

from loguru import logger
from PySide6.QtCore import QThread, Signal

from _coders import run_prompt


class PromptWorker(QThread):
    """后台执行 prompt 线程"""

    error = Signal(str)

    def __init__(self, prompt: str, cwd: str | None = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.cwd = cwd

    def set_working_directory(self, cwd: str):
        """设置工作目录"""
        self.cwd = cwd

    def run(self):
        """执行 prompt"""
        try:
            logger.debug(f"PromptWorker 开始执行:\n{self.prompt}")
            run_prompt(self.cwd, self.prompt)
            logger.debug("PromptWorker 执行完成")
        except Exception as exc:
            logger.error(f"PromptWorker 执行异常: {exc}")
            self.error.emit(str(exc))
