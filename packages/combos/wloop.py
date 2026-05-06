"""Combo WLoop 数据类"""

from string import Template

from transitions import Machine


class Episode:
    def __init__(self, id: str = "", filename: str = "", prompt: Template = None, component: str = ""):
        self.id = id
        self.filename = filename
        self.prompt = prompt if prompt is not None else Template("")
        self.component = component


class WLoop:
    """WLoop 循环执行数据类（Domain 层）

    状态机的状态：
    - IDLE: 初始/等待状态（特殊节点，不渲染）
    - "wloop": Episode 状态（可执行，渲染 SoloRunner）
    - FINISHED: 完成状态（特殊节点，不渲染）

    状态流转：IDLE → wloop → wloop → ... → FINISHED → IDLE
    """

    EPISODES = [
        Episode(
            id="wloop",
            filename=".agents/workflows/w-execute/WORKFLOW.md",
            prompt=Template("加载并执行 $filename"),
            component="WLoopSoloEpisode",
        ),
    ]
    LOOP = 3

    def __init__(self, working_directory: str = ""):
        self.working_directory = working_directory
        self.episodes = self.EPISODES.copy()
        self._count = 0

        """
        State Machine:

                          [next, count<LOOP]
                                ┌────┐
                                │    │
                                ▼    │
        IDLE ─────────────► wloop ─────────────► FINISHED
          ▲                     │                      │
          │                     │                      │
          └───────[reset]───────┴──────────────────────┘

        Transitions:
            - next(IDLE → wloop): count=1, return "wloop"
            - next(wloop → wloop): count+=1, return "wloop" (if count < LOOP)
            - next(wloop → FINISHED): return "FINISHED" (if count >= LOOP)
            - reset(any → IDLE): count=0
        """
        Machine(
            model=self,
            states=["IDLE", "wloop", "FINISHED"],
            initial="IDLE",
            transitions=[
                {"trigger": "next", "source": "IDLE", "dest": "wloop"},
                {"trigger": "next", "source": "wloop", "dest": "wloop", "conditions": "_can_continue"},
                {"trigger": "next", "source": "wloop", "dest": "FINISHED", "conditions": "_should_finish"},
                {"trigger": "reset", "source": "*", "dest": "IDLE"},
            ],
        )

    def _can_continue(self) -> bool:
        return self._count < self.LOOP

    def _should_finish(self) -> bool:
        return self._count >= self.LOOP

    def next(self) -> str:
        """触发状态转换，返回指令（当前状态）"""
        self.trigger("next")
        
        if self.state == "wloop":
            self._count += 1
            print(f"[WLoop] Execute episode 'wloop' (count={self._count}/{self.LOOP})")
        
        return self.state

    def reset(self) -> str:
        """重置状态机，返回 IDLE"""
        self._count = 0
        self.trigger("reset")
        return self.state