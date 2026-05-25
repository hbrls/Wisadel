"""Combo ALoop 数据类"""

from string import Template

from transitions import Machine


class Episode:
    def __init__(self, id: str = "", filename: str = "", prompt: Template = None, component: str = ""):
        self.id = id
        self.filename = filename
        self.prompt = prompt if prompt is not None else Template("")
        self.component = component


class ALoop:
    """ALoop 循环执行数据类（Domain 层）

    状态机的状态：
    - IDLE: 初始/等待状态（特殊节点，不渲染）
    - "aloop": Episode 状态（可执行，渲染 SoloRunner）
    - "checkdone": 检查完成状态
    - FINISHED: 完成状态（特殊节点，不渲染）

    状态流转：IDLE → aloop → checkdone → aloop → ... → FINISHED → IDLE
    """

    EPISODES = [
        Episode(
            id="aloop",
            filename=".agents/workflows/a-execute/WORKFLOW.md",
            prompt=Template("加载并执行 $filename"),
            component="ALoopSoloEpisode",
        ),
        Episode(
            id="checkdone",
            filename=".context/.done/",
            prompt=Template("CHECK_HAS_DIR: $filename"),
            component="ALoopSoloEpisode",
        ),
    ]
    LOOP = 10

    def __init__(self):
        self.episodes = self.EPISODES.copy()
        self._count = 0
        self._last_result = None
        self._done = False

        """
        State Machine:

              next          next           next
        IDLE ──────► aloop ──────► checkdone ──────► aloop ──────► ...
           ▲                                          │
           │                                          │ (count >= LOOP)
           └────────────────── reset ─────────────────┴──────────► FINISHED

        Transitions:
            - next(IDLE → aloop): return "aloop"
            - next(aloop → checkdone): return "checkdone"
            - next(checkdone → aloop): count+=1, return "aloop" (if count < LOOP)
            - next(checkdone → FINISHED): return "FINISHED" (if count >= LOOP)
            - reset(any → IDLE): count=0
        """
        Machine(
            model=self,
            states=["IDLE", "aloop", "checkdone", "FINISHED"],
            initial="IDLE",
            transitions=[
                {"trigger": "next", "source": "IDLE", "dest": "aloop"},
                {"trigger": "next", "source": "aloop", "dest": "checkdone"},
                {"trigger": "next", "source": "checkdone", "dest": "aloop", "conditions": "_can_continue"},
                {"trigger": "next", "source": "checkdone", "dest": "FINISHED", "conditions": "_should_finish"},
                {"trigger": "reset", "source": "*", "dest": "IDLE"},
            ],
        )

    def _can_continue(self) -> bool:
        return self._count < self.LOOP and not self._done

    def _should_finish(self) -> bool:
        return self._count >= self.LOOP or self._done

    def next(self, result=None) -> str:
        """触发状态转换，返回指令（当前状态）

        Args:
            result: 执行结果。PASS 继续循环，DONE 提前结束。
        """
        print(f"[ALoop] next() called with result={result}")
        self._last_result = result

        if self.state == "checkdone":
            if result == "YES":
                result = "DONE"
            elif result == "NO":
                result = "PASS"

        self._done = result == "DONE"

        if self.state == "checkdone" and result != "DONE":
            self._count += 1

        self.trigger("next")

        if self.state == "aloop":
            print(f"[ALoop] Execute episode 'aloop' (count={self._count}/{self.LOOP})")

        return self.state

    def reset(self) -> str:
        """重置状态机，返回 IDLE"""
        self._count = 0
        self._done = False
        self.trigger("reset")
        return self.state
