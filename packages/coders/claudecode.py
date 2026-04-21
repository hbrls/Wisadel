"""ClaudeCode 命令执行模块 - Claude AI 集成的代码处理功能

此模块提供与 Claude AI 集成的代码处理功能。
"""

import tempfile

from loguru import logger

from coders._command_coder import _CommandCoder


class ClaudeCode(_CommandCoder):
    """Claude AI 代码处理器"""

    @classmethod
    def probe(cls) -> None:
        """探测 claude 命令是否可用"""
        cwd = tempfile.gettempdir()
        result = _CommandCoder.execute_command(cwd, "claude --version")

        if result is None:
            logger.error("claude 探针失败: 命令执行异常")
            return

        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"claude 探针成功: {result.stdout.strip()}")
        else:
            logger.error("claude 探针失败: 未找到 claude 命令或执行出错")
