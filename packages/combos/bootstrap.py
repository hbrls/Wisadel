"""Combo Bootstrap 数据类"""

from string import Template

from transitions import Machine


class Episode:
    def __init__(self, id: str = "", filename: str = "", prompt: Template = None, component: str = ""):
        self.id = id
        self.filename = filename
        self.prompt = prompt if prompt is not None else Template("")
        self.component = component


class Bootstrap:
    """Bootstrap 顺序执行数据类（Domain 层）

    单向线性有限状态机：按 PHASES 数组依次推进，每次 next() 吐一个 Episode ID。
    同一 Episode ID 可在 PHASES 中出现多次，条件函数查阅 PHASES[_step] 决定路由。
    """

    EPISODES = [
        Episode(
            id="lens-ceo",
            filename=".agents/lens/ceo/LENS.md",
            prompt=Template(
                "加载并采用 $filename 视角。\n"
                "加载并遵守 `.agents/skills/bootstrap/SKILL.md` 运作规则。\n"
                "开始本回合的思考。"
            ),
            component="BootstrapSoloEpisode",
        ),
        Episode(
            id="lens-engineer",
            filename=".agents/lens/engineer/LENS.md",
            prompt=Template(
                "加载并采用 $filename 视角。\n"
                "加载并遵守 `.agents/skills/bootstrap/SKILL.md` 运作规则。\n"
                "开始本回合的思考。"
            ),
            component="BootstrapSoloEpisode",
        ),
        Episode(
            id="committer",
            filename=".agents/lens/committer/LENS.md",
            prompt=Template(
                "加载并采用 $filename 视角。\n"
                "加载并遵守 `.agents/skills/bootstrap/SKILL.md` 运作规则。\n"
                "开始本回合的思考。"
            ),
            component="BootstrapSoloEpisode",
        ),
    ]

    PHASES = ["lens-ceo", "lens-engineer", "committer", "lens-ceo", "lens-engineer", "committer"]

    def __init__(self, working_directory: str = ""):
        self.working_directory = working_directory
        self.episodes = self.EPISODES.copy()
        self._step = 0

        """
        State Machine:

        IDLE ──► lens-ceo ──► lens-engineer ──► committer ──► lens-ceo ──► lens-engineer ──► committer ──► FINISHED
          ▲                                                                                               │
          └────────────────────────────────────[reset]─────────────────────────────────────────────────────┘

        同一 Episode ID 可出现多次，条件函数查阅 PHASES[_step] 决定下一个目标。
        """
        Machine(
            model=self,
            states=["IDLE", "lens-ceo", "lens-engineer", "committer", "FINISHED"],
            initial="IDLE",
            transitions=[
                {"trigger": "next", "source": "IDLE", "dest": "lens-ceo"},
                {"trigger": "next", "source": "lens-ceo", "dest": "lens-engineer", "conditions": "_next_is_engineer"},
                {"trigger": "next", "source": "lens-ceo", "dest": "committer", "conditions": "_next_is_committer"},
                {"trigger": "next", "source": "lens-ceo", "dest": "FINISHED", "conditions": "_is_last_step"},
                {"trigger": "next", "source": "lens-engineer", "dest": "committer", "conditions": "_next_is_committer"},
                {"trigger": "next", "source": "lens-engineer", "dest": "lens-ceo", "conditions": "_next_is_ceo"},
                {"trigger": "next", "source": "lens-engineer", "dest": "FINISHED", "conditions": "_is_last_step"},
                {"trigger": "next", "source": "committer", "dest": "lens-ceo", "conditions": "_next_is_ceo"},
                {"trigger": "next", "source": "committer", "dest": "FINISHED", "conditions": "_is_last_step"},
                {"trigger": "reset", "source": "*", "dest": "IDLE"},
            ],
        )

    def _next_is_ceo(self) -> bool:
        return self._step < len(self.PHASES) and self.PHASES[self._step] == "lens-ceo"

    def _next_is_engineer(self) -> bool:
        return self._step < len(self.PHASES) and self.PHASES[self._step] == "lens-engineer"

    def _next_is_committer(self) -> bool:
        return self._step < len(self.PHASES) and self.PHASES[self._step] == "committer"

    def _is_last_step(self) -> bool:
        return self._step >= len(self.PHASES)

    @property
    def episode_ids(self) -> list[str]:
        return [ep.id for ep in self.episodes]

    @property
    def current_episode_index(self) -> int:
        if self.state in self.episode_ids:
            return self.episode_ids.index(self.state)
        return -1

    def next(self) -> str:
        self.trigger("next")
        if self.state not in ("FINISHED", "IDLE"):
            self._step += 1
            print(f"[Bootstrap] Execute episode '{self.state}' (step={self._step}/{len(self.PHASES)})")
        return self.state

    def reset(self) -> str:
        self._step = 0
        self.trigger("reset")
        return self.state
