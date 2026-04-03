-- Wisadel Rime Extension
-- Rime + Lua 学习项目 - 分阶段启用

-- ============ 阶段 1：Processor 基础 ============
function wisadel_key_processor(key, env)
    log.info("[wisadel] key: " .. key.keycode)
    return 2
end

-- ============ 阶段 2：Translator 生成自定义编码 ============
function date_translator(input, seg)
    if input == "date" then
        --- Candidate(type, start, end, text, comment)
        yield(Candidate("date", seg.start, seg._end, os.date("%Y年%m月%d日"), " 日期"))
    end
end

-- ============ 阶段 3：Filter 修改候选词 ============
-- function wisadel_filter(input, env)
--     local count = 0
--     for cand in input:iter() do
--         log.info("[wisadel] filter: " .. cand.text)
--         cand.comment = "[wisadel]" .. (cand.comment or "")
--         yield(cand)
--         count = count + 1
--     end
--     log.info("[wisadel] filter done, count: " .. count)
-- end

-- ============ 阶段 5：commit 拦截 ============
function wisadel_commit(env)
    local text = env.composer:get_preedit_text()
    if text then
        log.info("[wisadel] commit: " .. text)
    end
end
