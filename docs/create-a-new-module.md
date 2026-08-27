# 创建新模块指南

> updated_by: Codex
> updated_at: 2026-08-27 17:33:21

本指南介绍如何在 wishadel 项目中创建一个新的 Python 模块包。

## 目录结构

```
packages/
├── coders/              # 代码执行模块
├── combos/              # Combo 模块（参考实现）
├── wwm/                 # WWM 桌面应用（消费方）
│   ├── requirements.txt # 依赖声明
│   └── main.py
└── w-execute/           # w-execute 桌面应用（消费方）
    ├── requirements.txt # 依赖声明
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

### 4. 更新消费方依赖

确定实际消费该模块的活跃应用，并编辑对应的依赖文件：

- `packages/wwm/requirements.txt`
- `packages/w-execute/requirements.txt`

仅在实际依赖该模块的应用中添加 editable install 依赖；如果两个应用都依赖该模块，则两个文件都需要更新：

```diff
 # Internal packages (editable install)
+-e ../{module_name}
 -e ../combos
```

### 5. 在消费方安装并验证

在实际消费方安装所有依赖并验证导入。下例中的 `{consumer}` 为 `wwm` 或 `w-execute`：

> 以下命令仅供开发者在 PyCharm 手工管理的环境中执行。Agent 禁止执行 Python、pip、构建或依赖管理命令，只能进行静态检查。

```bash
pip install -r packages/{consumer}/requirements.txt

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
- [ ] 所有实际消费方的 `requirements.txt` 均包含 `-e ../{module_name}`
- [ ] `pip install -r packages/{consumer}/requirements.txt` 成功（**修改过 pyproject.toml 后必须由开发者重新执行**）
- [ ] `python -c "from {module_name}.{sub} import ..."` 成功
- [ ] 验证**禁止**使用 `from {module_name} import`

---

## 常见问题

### Q: `from {module_name} import` 可以工作吗？

**A**: **禁止使用**。必须在 `__init__.py` 中移除所有导出，所有导入必须使用完整路径。

### Q: `from .xxx import` 相对导入失败

**A**: 由于 `package-dir` 映射，相对导入会破坏路径。建议使用绝对导入 `from {module_name}.xxx`。

### Q: 用了 `find` 方式，`{module_name}.providers` 等子包无法访问

**A**: 这是 `find` + 同名子目录组合导致的陷阱。如果包目录内有与包同名的子目录（如 `packages/{module_name}/{module_name}/`），使用：

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["{module_name}*"]
```

setuptools 可能会把内层同名目录误识别为顶层包，导致外层 `__init__.py` 和兄弟子包被忽略，表现为子包导入失败。

**正确做法**：始终使用 `package-dir` 映射方式（见上文），**禁止使用 `find` 方式**。

### Q: 修改了 `pyproject.toml`，但 `import` 行为没有变化

**A**: `egg-info` 已过期。`pyproject.toml` 变更后，setuptools 不会自动更新已安装的包元数据，必须重新执行：

```bash
pip install -r packages/{consumer}/requirements.txt
```

可通过检查 `packages/{module_name}/{module_name}.egg-info/SOURCES.txt` 确认内容是否包含期望的子包。

---

## 参考实现

- **combos 模块**: `packages/combos/` - 简单的 prompt 模板包
