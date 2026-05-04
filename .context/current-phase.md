# PHASE-400: 改造成 QFluentWidgets

## TASK-200: 重命名 Runbook -> Combo

- 目录 `packages/runbooks/` 重命名为 `packages/combos/`，包名同步更新
- 文件重命名：`combos/task.py` → `combos/plan.py`，`runbook_*_container.py` → `combo_*_container.py`，`task_page.py` → `plan_page.py`
- 类名重命名：`Task` → `Plan`，`TaskStateMachine` → `PlanStateMachine`，`ComboTaskContainer` → `ComboPlanContainer`，`TaskPage` → `PlanPage`，`TaskSoloEpisode` → `PlanSoloEpisode`
- 全局导入、依赖声明（requirements.txt）、文档（docs/*）已同步更新
- 全局无 `runbooks`/`Runbook` 引用残留

## TASK-300: 引入状态机 transitions

- 逐个 Combo 迁移：TASK-301(WLoop) → TASK-303(Plan) → TASK-304(Bootstrap)，每个完成后人工验收再推进
- 核心决策：`trigger()` 模式替代 `next_action()`、回调解耦 Container、不抽基类、动态构建 transitions
- 影响范围：`packages/combos/*.py`（3 个状态机）、`packages/wwm/ui/containers/combo_*_container.py`（3 个 Container）、`requirements.txt`

## TASK-301: WLoop 引入 transitions 状态机

> updated_by: Kilo - GLM-5
> updated_at: 2026-05-06 16:01:00

### 实现方案

- 状态机状态 = Episode ID：IDLE（初始）、wloop（可执行）、FINISHED（完成）
- 状态流转：IDLE → wloop → wloop → ... → FINISHED → IDLE
- 指令驱动模式：`wloop.next()` 返回当前状态作为指令，Container 通过 `_execute_instruction()` 执行
- Container 不决策，只执行指令：指令是 Episode ID → 执行 Episode；指令是 FINISHED → 重置状态机、解锁 UI
- 移除旧引用：WLoopStateMachine/next_action/current_count/notify_run_completed 已全部清理
- 代码位置：`packages/combos/wloop.py`（Machine 定义）、`packages/wwm/ui/containers/combo_wloop_container.py`（指令执行）

### 验收结果

**人工验收通过** ✅（2026-05-06 15:48）
- WLoop Play 流程：点击 Play → 多轮自动执行 → 完成后自动重置
- Solo 按钮在 Play 期间锁定，完成后解锁
- 状态守卫：FINISHED 状态下调用 next() 不产生非法状态
- 日志正确显示轮次

## TASK-302: 显示 wloop 步骤

> updated_by: Kilo - GLM-5
> updated_at: 2026-05-06 17:45:00

### 实现方案

- 创建 `ComboStates` 组件（`packages/wwm/ui/components/combo_states.py`）：纯展示组件，持有 `ListWidget`，提供 `append(state)` slot
- Container 内部持有 `ComboStates`，左右分栏布局（左侧面板 + separator + StateHistory）
- 移除 `instruction_emitted` 信号：状态历史由 Container 直接管理，不再暴露给 Page
- Page 简化为只持有 Container：移除右侧面板、separator、信号监听、标题
- Solo 按钮不参与右侧显示：通过 `_play_active` 标志控制，仅 Play 流程记录状态
- 代码位置：`packages/wwm/ui/components/combo_states.py`、`packages/wwm/ui/containers/combo_wloop_container.py`、`packages/wwm/ui/pages/wloop_page.py`

### 验收结果

- **人工验收通过** ✅：左右分栏显示正常，竖线两侧 margin 对称（16px）
- **人工验收通过** ✅：点击 Play 后右侧列表依次显示 IDLE → wloop → wloop → wloop → FINISHED → IDLE
- **人工验收通过** ✅：Solo 执行不影响右侧步骤列表
