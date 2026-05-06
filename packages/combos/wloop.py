"""Combo WLoop 数据类"""

from dataclasses import dataclass, field
from string import Template
from typing import List


@dataclass
class Episode:
    id: str = ""
    filename: str = ""
    prompt: Template = field(default_factory=lambda: Template(""))


@dataclass
class WLoopStateMachine:
    """WLoop 循环执行状态机

    管理循环执行的计数和状态。
    持有对 WLoop 的引用以读取 loop 值。
    
    current_count 代表"已启动的 Worker 数"（预定执行次数）。
    """

    wloop: "WLoop" = None
    current_count: int = 0

    def next_action(self) -> str:
        """查询下一步动作，并在决定执行时预定计数

        Returns:
            "start_run": 首次执行，预定后 count = 1
            "continue_run": 继续循环，预定后 count < loop
            "stop": 已达上限，count >= loop
        """
        loop = self.wloop.loop if self.wloop else 5
        if self.current_count >= loop:
            return "stop"
        self.current_count += 1
        if self.current_count == 1:
            return "start_run"
        return "continue_run"

    def notify_run_completed(self):
        """通知执行完成（用于日志/显示，不增加计数）"""
        pass

    def reset(self):
        """重置状态"""
        self.current_count = 0


@dataclass
class WLoop:
    """WLoop 循环执行数据类（Domain 层）

    纯业务逻辑，不涉及 UI。
    """

    working_directory: str = ""
    episodes: List[Episode] = field(default_factory=lambda: [
        Episode(id="wloop", filename=".agents/workflows/w-execute/WORKFLOW.md", prompt=Template("加载并执行 $filename")),
    ])
    loop: int = 3

    def __post_init__(self):
        self.state_machine = WLoopStateMachine(wloop=self)
