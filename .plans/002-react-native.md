# React Native Windows Exe 证明计划

## 目标
证明 React Native Windows 可以构建成独立的 exe 文件，作为 MVP2 浮窗润色输入法的 GUI 基础。不涉及润色功能，仅验证 GUI 框架的可行性。只支持 Windows 平台，不包括 Android 或 iOS。

## 步骤

### 1. **环境检查** ✅
- ✅ Node.js: **v20.19.4** (要求 >= 18.0)
- ✅ npm: **10.8.2** (要求 >= 9.0)
- ✅ Visual Studio: **2026 Community** with MSBuild 18.0.5
- ✅ Windows SDK: **10.0.26100.0** (要求 >= 10.0.19041.0)

### 2. **初始化项目结构**（准备阶段）✅

**版本要求**（必须匹配）：
| 包 | 版本 |
|---|---|
| react-native | **0.81.5** |
| react-native-windows | **0.81.2** |

- 创建项目（使用指定版本）：
```powershell
cd packages
npx @react-native-community/cli@latest init app --version 0.81.5 --skip-install
cd app
```
- 安装依赖：
  ```powershell
  npm install
  ```
- 添加 Windows 支持（0.76+ 的新方法）：
  ```powershell
  npm install --save-dev react-native-windows@0.81.2
  npx @react-native-community/cli init-windows --overwrite
  ```
- 验证项目结构：
  - `windows/` 目录已创建
  - `package.json` 包含 `react-native-windows@0.81.2` 依赖
  - 确认 `metro.config.js` 存在
- 注意：仅配置 Windows 支持，Android/iOS 相关文件可忽略

### 3. **开发模式验证**（Dev Mode 测试）
- 修改 `App.tsx`，创建简单测试界面：
  - 显示 "Hello from Wishadel" 标题
  - 显示一个按钮（用于验证交互，无实际功能）
- 使用 React Native 基础组件：`View`, `Text`, `Button`
- 启动开发模式：
  ```powershell
  npx react-native run-windows
  ```
- 验证检查项：
  - ✅ Metro bundler 启动成功
  - ✅ 应用窗口正常显示
  - ✅ 热重载工作正常
- 更新 `package.json` 添加构建脚本（为步骤4准备）：
  ```json
  "scripts": {
    "windows": "react-native run-windows",
    "windows-release": "react-native run-windows --release --no-launch"
  }
  ```

### 4. **构建 Release Exe**
- 清理之前的构建：
  ```powershell
  Remove-Item windows/x64 -Recurse -Force -ErrorAction SilentlyContinue
  ```
- 构建 Release 版本：
  ```powershell
  npx react-native run-windows --release --no-launch --arch x64
  ```
- 构建输出位置：`windows/x64/Release/app/`
- 关键文件：
  - `app.exe` - 主程序
  - `app/` 子目录 - 资源和 DLL
- 验证 JS bundle 已打包：检查 `Bundle/` 或 `Assets/` 目录

### 5. **测试和验证**
- 直接运行 exe 文件：`./windows/x64/Release/app/app.exe`
- 验证检查项：
  - ✅ 窗口正常显示
  - ✅ UI 渲染正确（标题和按钮显示）
  - ✅ 按钮可点击（即使无功能）
  - ✅ 无需 Metro bundler 运行
  - ✅ 可在其他 Windows 机器上运行（需携带整个 Release 目录）
- 记录 exe 文件大小和启动时间
- 测试独立运行：复制整个 `app/` 目录到其他位置测试

## 依赖和环境要求

### 必需
- **Node.js** >= 18.0
- **npm** >= 9.0
- **Visual Studio 2022** (Community 版本即可)
  - 工作负载："使用 C++ 的桌面开发"
  - Windows 10 SDK (10.0.19041.0 或更高)
- **Windows 10** (版本 1809+) 或 **Windows 11**

### 可选
- **Chocolatey** (用于快速安装依赖)
- **VS Code** + React Native Tools 扩展

## 输出

### 主要产物
- **可执行 exe 文件**：`packages/app/windows/x64/Release/app/app.exe`
- **完整应用包**：`packages/app/windows/x64/Release/app/` 目录（包含所有 DLL 和资源）
- **项目源码**：`packages/app/` 目录

### 文档
- `packages/app/BUILD.md` - 构建说明
- 构建日志和错误记录
- exe 文件大小和性能指标

## 已知风险和缓解

### 风险
1. **构建时间长**：首次 Release 构建可能需要 15-30 分钟
   - 缓解：使用 `--no-launch` 参数，后台构建
2. **NuGet 包还原失败**：网络问题或配置问题
   - 缓解：配置国内 NuGet 镜像源
3. **exe 文件体积大**：可能 50-150MB+
   - 缓解：这是 POC，暂不优化

### 备选方案
- 如果 React Native Windows 构建过于复杂或不稳定，考虑：
  - Electron + React
  - Tauri + React
  - WinUI 3 + WebView2

## 后续计划
- ✅ **阶段 1**：证明 exe 可构建和运行（本计划）
- 🔲 **阶段 2**：集成 Native Module 用于文本插入
- 🔲 **阶段 3**：实现浮窗 UI 和快捷键监听
- 🔲 **阶段 4**：集成 AI 润色功能
- 🔲 **阶段 5**：打包和分发优化
