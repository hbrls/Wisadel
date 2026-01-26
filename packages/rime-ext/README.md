# Wisadel 文本润色工具

这是使用 Rime + Lua 的 Wisadel 文本润色工具。

## 设置

1. 在 Windows 上安装 Rime (Weasel)。
2. 将 `wisadel.schema.yaml`、`wisadel.lua`、`wisadel.custom.yaml` 和 `rime.lua` 复制到你的 Rime 用户目录（例如 `%APPDATA%\Rime\`）。
3. 部署 Rime 配置。
4. 部署后，右键 Rime 托盘图标，选择“方案” > “维什戴尔” 以切换到该方案。

## 使用方法

- 输入包含 "hello" 的文本。
- 选择候选以查看润色结果（"hello" 替换为 "hi"）。
- 按空格或回车确认上屏。

## 注意事项

- 这是用于测试 Rime + Lua 集成的极简实现。
- 下一步：集成 pre-commit 钩子以完全符合规格。