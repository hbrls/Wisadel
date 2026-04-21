---
name: execute
description: 执行并完成任务 `.context/current-task.md`，将任务标记为完成，将相关的过程文档上传更新。
metadata:
  version: 0.0.3
---

# Execute

**FAIL-FAST REQUIREMENT** Check if the tools exist, stop immediately and exit on any error.

```bash
$ backstage-gitea plan --help
```

## Initialization

**MUST** 读取相关的 `Plan` 信息在 `.context/current-plan-metadata.yaml` 和 `.context/current-plan.md`。读取失败时必须立刻停止并退出。

**MUST** 读取相关的 `Phase` 信息在 `.context/current-phase-metadata.yaml` 和 `.context/current-phase.md`。读取失败时必须立刻停止并退出。

**MUST** 读取相关的 `Task` 信息在 `.context/current-task-metadata.yaml` 和 `.context/current-task.md`。读取失败时必须立刻停止并退出。

## Workflow

- Step 1: 开始执行任务 `.context/current-task.md`。

- Step 2: 执行过程中如果发现需要更新 `Plan` 或 `Phase` 或 `Task`，应该在任务步骤中明确说明，并更新到 `.context/current-plan.md` 或 `.context/current-phase.md` 或 `.context/current-task.md` 或其它相关文档或代码。

- Step 3: 任务完成后，使用 `backstage-gitea` 工具将 `.context/current-task.md` 上传更新。

```bash
# IF Task PASS
$ backstage-gitea plan PUT-PASS /:appName/:planId/:phaseId/:taskId --context .context/current-task.md

# IF Task FAIL
$ backstage-gitea plan PUT-FAIL /:appName/:planId/:phaseId/:taskId --context .context/current-task.md
```

- Step 4: 如果执行过程中有更新 `Phase` 或 `Plan`，使用 `backstage-gitea` 工具将 `.context/current-phase.md` 和 `.context/current-plan.md` 上传更新。

```bash
$ backstage-gitea plan PUT /:appName/:planId/:phaseId --context .context/current-phase.md

$ backstage-gitea plan PUT /:appName/:planId --context .context/current-plan.md
```

## Rules

**MUST** 应该在一个 `Agent Session` 中执行。如果 Context 即将用尽，必须立刻停止并退出。这种场景说明 Task 拆分有误。

**MUST** 执行过程中如识别到关键变更，必须立刻停止并退出。这种场景说明 Design 需要更新。

- 按顺序执行任务，从第一个 `- [ ]` 开始。
- 一次只执行一个步骤条目。
- 完成后将对应条目从 `- [ ]` 更新为 `- [x]`。
- 确认所有步骤条目已按预期完成并标注完成状态。
