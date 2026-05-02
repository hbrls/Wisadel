"""Runbook Bootstrap 数据类"""

from dataclasses import dataclass, field
from string import Template
from typing import List

from runbooks.task import Episode


@dataclass
class BootstrapStateMachine:
    """Bootstrap 顺序执行状态机：lens-ceo → lens-engineer 循环 N 轮

    根据 episodes 和 loop 参数动态生成 phase 列表。
    Phase 命名：{episode_id}-{round}，如 lens-ceo-1, lens-engineer-1, lens-ceo-2, ...
    """

    bootstrap: "Bootstrap" = None
    current_phase: str = "idle"

    def _build_phases(self) -> list[str]:
        """根据 episodes 和 loop 动态生成 phase 列表"""
        episodes = self.bootstrap.episodes if self.bootstrap else []
        loop = self.bootstrap.loop if self.bootstrap else 1
        phases = []
        for round_num in range(1, loop + 1):
            for ep in episodes:
                phases.append(f"{ep.id}-{round_num}")
        return phases

    def _get_phase_episode_map(self) -> dict[str, int]:
        """根据 episodes 和 loop 动态生成 phase → episode index 映射"""
        episodes = self.bootstrap.episodes if self.bootstrap else []
        loop = self.bootstrap.loop if self.bootstrap else 1
        mapping = {}
        for round_num in range(1, loop + 1):
            for i, ep in enumerate(episodes):
                mapping[f"{ep.id}-{round_num}"] = i
        return mapping

    def next_action(self) -> str:
        phases = self._build_phases()
        if not phases:
            return "stop"
        if self.current_phase == "idle":
            self.current_phase = phases[0]
            return "start_run"
        try:
            idx = phases.index(self.current_phase)
        except ValueError:
            return "stop"
        next_idx = idx + 1
        if next_idx >= len(phases):
            return "stop"
        self.current_phase = phases[next_idx]
        return "continue_run"

    def get_current_episode_index(self) -> int:
        """获取当前 phase 对应的 episode 索引"""
        return self._get_phase_episode_map().get(self.current_phase, -1)

    def reset(self):
        """重置为 idle 状态"""
        self.current_phase = "idle"


@dataclass
class Bootstrap:
    working_directory: str = ""
    loop: int = 2
    episodes: List[Episode] = field(default_factory=lambda: [
        Episode(id="lens-ceo", filename=".agents/lens/ceo/LENS.md", prompt=Template(
            "加载并采用 $filename 视角。\n"
            "加载并遵守 `.agents/skills/bootstrap/SKILL.md` 运作规则。\n"
            "开始本回合的思考。"
        )),
        Episode(id="lens-engineer", filename=".agents/lens/engineer/LENS.md", prompt=Template(
            "加载并采用 $filename 视角。\n"
            "加载并遵守 `.agents/skills/bootstrap/SKILL.md` 运作规则。\n"
            "开始本回合的思考。"
        )),
    ])

    def __post_init__(self):
        self.state_machine = BootstrapStateMachine(bootstrap=self)
