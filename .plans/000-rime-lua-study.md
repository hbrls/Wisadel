# Rime + Lua 开发学习计划

## 目标
通过动手实践，从零掌握 Rime + Lua 开发模式。

## 学习方式
**做中学**：每个阶段都有具体的代码任务，完成即掌握。

---

### 开发规范

**命名规范**：
- 使用 `rime.lua` 作为全局脚本入口
- 所有函数使用前缀 `wisadel_` 区分，如 `wisadel_key_processor`

**日志规范**：
- 使用 `log.info()` 打日志，不使用 `print()`

**示例**：
```lua
function wisadel_key_processor(key, env)
    log.info("[wisadel] key: " .. key.keycode)
    return 2
end
```

**Processor 基础验证**：输入 "date" 显示日期

**Schema 配置规范**：
- 不定义自己的 schema
- 在 `luna_pinyin.custom.yaml` 里面做 patch

### 阶段 1：Processor 基础（30 分钟）✅ 已完成

**任务**：实现按键监听，打印按键信息

**步骤**：

1. **创建 `rime.lua` 文件**（Rime 用户目录）：
   ```lua
   function wisadel_key_processor(key, env)
       log.info("[wisadel] key: " .. key.keycode)
       return 2
   end
   ```

2. **在 `luna_pinyin.custom.yaml` 添加 patch**：
   ```yaml
   patch:
     "engine/processors/+":
       - lua_processor@wisadel_key_processor
   ```
   （key 包含 `+`，需用引号包裹；使用全局函数，无需指定 `script` 和 `function`）

3. **重新部署**

**验证**：部署后在任意输入框按键，日志输出按键信息

常见按键编码：
- `0` - 空键或特殊键
- `65293` - Enter 回车键
- `65474` - Backspace 退格键
- `32` - 空格键

注意：Rime 日志文件可能只保留最后几千行，如需查看所有按键请实时监控日志。

---

### 阶段 2：Translator 生成自定义编码（1 小时）✅ 已完成

**任务**：实现一个简单的中英混输

1. 在 `rime.lua` 中添加 `date_translator` 函数：
   ```lua
   function date_translator(input, seg)
       if input == "date" then
           yield(Candidate("date", seg.start, seg._end, os.date("%Y年%m月%d日"), " 日期"))
       end
   end
   ```

2. 在 `luna_pinyin.custom.yaml` 添加 patch：
   ```yaml
   patch:
     "engine/translators/+":
       - lua_translator@date_translator
   ```

**验证**：输入 "date"，候选显示当前日期（如 "2025年02月02日"）

---

### 阶段 3：Filter 修改候选词（1 小时）⏳ 跳过

**任务**：在候选词后添加 `[wisadel]` 注释

1. 在 `rime.lua` 中添加 `wisadel_filter` 函数：
   ```lua
   function wisadel_filter(input, env)
       local count = 0
       for cand in input:iter() do
           log.info("[wisadel] filter: " .. cand.text)
           cand.comment = "[wisadel]" .. (cand.comment or "")
           yield(cand)
           count = count + 1
       end
       log.info("[wisadel] filter done, count: " .. count)
   end
   ```

2. 在 `luna_pinyin.custom.yaml` 添加 patch：
   ```yaml
   patch:
     "engine/filters/+":
       - lua_filter@wisadel_filter
   ```

**验证**：输入拼音，候选词显示 "[wisadel]xxx"

**注意**：filter 生命周期在某些场景下可能不生效（输入拼音时 count: 0），原因待排查

---

### 阶段 4：Context 变量（1.5 小时）⏳ 跳过

---

### 阶段 5：commit 拦截（1 小时）

**任务**：在上屏前修改文本

1. 在 `rime.lua` 中添加 `wisadel_commit` 函数：
   ```lua
   function wisadel_commit(env)
       local text = env.composer:get_preedit_text()
       if text then
           log.info("[wisadel] commit: " .. text)
       end
   end
   ```

2. 在 `luna_pinyin.custom.yaml` 添加 patch：
   ```yaml
   patch:
     "engine/commiters/+":
       - lua_committer@wisadel_commit
   ```

**验证**：输入文本后查看日志
---

## 学习成果检验

完成上述 5 个阶段后，应能够：
1. ✅ 独立创建和修改 Rime schema 配置
2. ✅ 使用 processor 拦截按键
3. ✅ 使用 translator 生成自定义编码
4. ✅ 使用 filter 修改候选词
5. ✅ 读写 Context 变量
6. ✅ 拦截 commit 修改上屏文本

**预期时间**：5-6 小时（可分 2-3 天完成）

---

## 参考资源

| 资源 | 链接 |
|------|------|
| Rime Lua 文档 | https://github.com/hchunhui/librime-lua |
| Rime 脚本示例 | https://github.com/rime/rime-lua-examples |
| 小狼毫文档 | https://rime.im/docs/ |
