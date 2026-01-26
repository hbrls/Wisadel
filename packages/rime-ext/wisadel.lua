-- Minimal test translator
function polish_translator(input, seg)
    print("Translator called with: " .. input)
    yield(Candidate("test", seg.start, seg._end, "test candidate", "test"))
end

return polish_translator