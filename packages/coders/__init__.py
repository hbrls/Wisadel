"""
Coders 模块

提供代码处理与分析功能。

注意：
- `KiloCode` 提供跨平台命令执行功能
- `ClaudeCode` 提供 Claude AI 集成的代码处理功能
- `run_command` 提供便捷的模块级命令执行函数（默认使用 KiloCode）
"""

from .claudecode import ClaudeCode
from .kilocode import KiloCode, probe, run_command, run_prompt, create_session

__all__ = [
    "KiloCode",
    "ClaudeCode",
    "probe",
    "run_command",
    "run_prompt",
    "create_session",
]
