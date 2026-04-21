---
name: sk-execute-task
description: Execute Workflow: .agents/workflows/sk-execute-task/WORKFLOW.md
metadata:
    version: 0.0.3
---

# Execute Task

**FAIL-FAST REQUIREMENT** 检查 `# LLM Coding Level Board`，当前使用基模的评分必须优于 `L2`。如果满足，回复 **所以 {实际使用的基模名称} 来砍，阿剑也不会生气**。如果不满足，必须立刻停止并退出。

Read and Execute the Workflow, strictly following the instructions in the file: `.agents/workflows/sk-execute-task/WORKFLOW.md`.
