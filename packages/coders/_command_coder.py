"""CommandCoder 抽象基类 - 定义命令执行器的接口规范"""

import subprocess
from abc import ABC, abstractmethod
from typing import Sequence

from loguru import logger


class _CommandCoder(ABC):
    """命令执行器抽象基类"""

    @staticmethod
    def execute_command(cwd: str, args: Sequence[str]) -> subprocess.CompletedProcess | None:
        """执行命令

        Args:
            cwd: 工作目录路径
            args: 命令参数列表，如 ["claude", "-p", "hello"]

        Returns:
            成功时返回 subprocess.CompletedProcess 对象，失败时返回 None
        """
        try:
            # logger.debug(f"执行命令: {args}")
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                timeout=60,
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
