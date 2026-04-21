"""CommandCoder 抽象基类 - 定义命令执行器的接口规范"""

import subprocess
import sys
from abc import ABC, abstractmethod

from loguru import logger

from coders.platform_utils import is_macos, is_windows


class _CommandCoder(ABC):
    """命令执行器抽象基类"""

    @staticmethod
    def execute_command(cwd: str, command: str) -> subprocess.CompletedProcess | None:
        """执行 shell 命令

        Args:
            cwd: 工作目录路径
            command: 要执行的命令字符串

        Returns:
            成功时返回 subprocess.CompletedProcess 对象，失败时返回 None

        Note:
            - Windows: 使用 powershell -Command 执行
            - macOS/Linux: 使用 bash -c 执行
        """
        if is_windows():
            args = ["powershell", "-Command", command]
            kwargs = {"encoding": "utf-8", "errors": "replace"}
        elif is_macos():
            args = ["bash", "-c", command]
            kwargs = {}
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return None

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=cwd,
                **kwargs,
            )
            return result
        except Exception as e:
            logger.error(f"命令执行异常: {type(e).__name__}: {e}")
            return None

    @classmethod
    @abstractmethod
    def probe(cls) -> None:
        """探测命令是否可用"""
        pass
