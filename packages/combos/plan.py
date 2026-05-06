"""Combo Plan 数据类"""

from dataclasses import dataclass, field
from string import Template
from typing import List


@dataclass
class Episode:
    id: str = ""
    filename: str = ""
    prompt: Template = field(default_factory=lambda: Template(""))


@dataclass
class PlanStateMachine:
    """Plan 顺序执行状态机：explore → execute → evaluate

    显式管理三个阶段的状态流转。
    """

    PHASES = ["explore", "execute", "evaluate"]

    plan: "Plan" = None
    current_phase: str = "idle"

    def next_action(self) -> str:
        """推进到下一阶段并返回动作

        Returns:
            "start_run": 从 idle 进入 explore
            "continue_run": 从 explore → execute，或 execute → evaluate
            "stop": evaluate 已完成，无下一阶段
        """
        if self.current_phase == "idle":
            self.current_phase = "explore"
            return "start_run"
        try:
            idx = self.PHASES.index(self.current_phase)
        except ValueError:
            return "stop"
        next_idx = idx + 1
        if next_idx >= len(self.PHASES):
            return "stop"
        self.current_phase = self.PHASES[next_idx]
        return "continue_run"

    def get_current_episode_index(self) -> int:
        """获取当前阶段对应的 episode 索引

        Returns:
            int: 0 (explore), 1 (execute), 2 (evaluate), -1 (idle/invalid)
        """
        try:
            return self.PHASES.index(self.current_phase)
        except ValueError:
            return -1

    def reset(self):
        """重置为 idle 状态"""
        self.current_phase = "idle"


@dataclass
class Plan:
    """执行计划数据类（Domain 层）

    纯业务逻辑，不涉及 UI。
    """
    working_directory: str = ""
    episodes: List[Episode] = field(default_factory=lambda: [
        Episode(id="sk-explore-plan", filename=".agents/workflows/sk-explore-task/WORKFLOW.md", prompt=Template("加载并执行 $filename")),
        Episode(id="sk-execute-plan", filename=".agents/workflows/sk-execute-task/WORKFLOW.md", prompt=Template("加载并执行 $filename")),
        Episode(id="sk-evaluate-plan", filename=".agents/workflows/sk-evaluate-task/WORKFLOW.md", prompt=Template("加载并执行 $filename")),
    ])

    def __post_init__(self):
        self.state_machine = PlanStateMachine(plan=self)
