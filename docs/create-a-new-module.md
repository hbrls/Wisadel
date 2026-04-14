# 创建新模块指南

> updated_by: Cascade - Claude-Sonnet-3.7
> updated_at: 2026-04-14 18:54:00

本指南介绍如何在 wishadel 项目中创建一个新的 Python 模块包。

## 目录结构

```
packages/
├── agents/          # Agent 模块（参考实现）
├── runbooks/        # Runbooks 模块（参考实现）
└── wwm/             # Windows Window Manager（消费方）
    ├── requirements.txt  # 依赖声明
    └── main.py
```

## 创建步骤

### 1. 创建包目录

```bash
mkdir -p packages/{module_name}
```

### 2. 创建 pyproject.toml

创建 `packages/{module_name}/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "{module_name}"
version = "0.1.0"

[tool.setuptools]
# 将 packages/{module_name}/ 目录映射为 {module_name} 包
# 这样 packages/{module_name}/{sub1}/ 就变成了 {module_name}.{sub1}
[tool.setuptools.package-dir]
"{module_name}" = "."

# 手动列出所有子模块（禁止使用 find_packages）
packages = [
    "{module_name}",
    "{module_name}.{sub1}",
    "{module_name}.{sub2}",
]
```

### 3. 创建包结构

```
packages/{module_name}/
├── __init__.py           # 主入口，**禁止导出任何公开 API**
├── pyproject.toml        # 包配置
├── {sub1}/               # 子模块 1
│   ├── __init__.py
│   └── ...
├── {sub2}/               # 子模块 2
│   ├── __init__.py
│   └── ...
└── tests/
    └── test_xxx.py
```

### 4. 更新消费者依赖

编辑 `packages/wwm/requirements.txt`，添加 editable install 依赖：

```diff
 # Internal packages (editable install)
+-e ../{module_name}
 -e ../agents
 -e ../runbooks
```

### 5. 在消费方安装并验证

在消费方（如 `packages/wwm`）安装所有依赖并验证导入：

```bash
pip install -r packages/wwm/requirements.txt

# 验证子模块导入（禁止使用根目录导入）
python -c "from {module_name}.{sub1} import Yyy; print(Yyy)"
```

---

## pyproject.toml 配置要点

### package-dir 映射机制

```toml
[tool.setuptools.package-dir]
"{module_name}" = "."
```

这行配置告诉 setuptools：将 `packages/{module_name}/` 目录（当前目录 `.`）视为 `{module_name}` 包。

**效果**：
- `packages/{module_name}/__init__.py` → `{module_name}.__init__`
- `packages/{module_name}/core.py` → `{module_name}.core`
- `packages/{module_name}/{sub1}/xxx.py` → `{module_name}.{sub1}.xxx`

### packages 手动列出子模块

setuptools **不会**自动发现子包，必须手动列出：

```toml
[tool.setuptools]
packages = [
    "{module_name}",              # 顶层包
    "{module_name}.{sub1}",       # 子模块
    "{module_name}.{sub2}",
]
```

**禁止使用 find_packages()**：因为它返回的是相对路径，添加前缀后可能重复或不正确。

---

## 验证清单

创建新模块后，确认以下检查点：

- [ ] `pyproject.toml` 存在且配置正确
- [ ] `packages` 列表手动包含所有子模块（不使用 find_packages）
- [ ] `package-dir` 映射正确
- [ ] `__init__.py` 不导出任何公开 API
- [ ] requirements.txt 包含 `-e ../{module_name}`
- [ ] `pip install -r packages/wwm/requirements.txt` 成功（**修改过 pyproject.toml 后必须重新执行**）
- [ ] `python -c "from {module_name}.{sub} import ..."` 成功
- [ ] 验证**禁止**使用 `from {module_name} import`

---

## 常见问题

### Q: `from {module_name} import` 可以工作吗？

**A**: **禁止使用**。必须在 `__init__.py` 中移除所有导出，所有导入必须使用完整路径。

### Q: `from .xxx import` 相对导入失败

**A**: 由于 `package-dir` 映射，相对导入会破坏路径。建议使用绝对导入 `from {module_name}.xxx`。

### Q: 用了 `find` 方式，`{module_name}.providers` 等子包无法访问

**A**: 这是 `find` + 同名子目录组合导致的陷阱。如果包目录内有与包同名的子目录（如 `packages/agents/agents/`），使用：

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["agents*"]
```

setuptools 会把**内层** `packages/agents/agents/` 误识别为顶层 `agents` 包，外层 `__init__.py` 和 `providers/`、`tools/` 等兄弟子包全部被忽略，表现为 `import agents.providers` 抛 `ModuleNotFoundError`。

**正确做法**：始终使用 `package-dir` 映射方式（见上文），**禁止使用 `find` 方式**。

### Q: 修改了 `pyproject.toml`，但 `import` 行为没有变化

**A**: `egg-info` 已过期。`pyproject.toml` 变更后，setuptools 不会自动更新已安装的包元数据，必须重新执行：

```bash
pip install -r packages/wwm/requirements.txt
```

可通过检查 `packages/{module_name}/{module_name}.egg-info/SOURCES.txt` 确认内容是否包含期望的子包。

---

## 参考实现

- **runbooks 模块**: `packages/runbooks/` - 简单的 prompt 模板包
- **agents 模块**: `packages/agents/` - 复杂的 Agent 框架包
