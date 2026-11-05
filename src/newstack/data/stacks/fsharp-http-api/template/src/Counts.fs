module Textstat.Counts

// Byte counting, the way wc does it: a "line" is a newline, a "word" is a run of
// bytes that is not one of the six ASCII separators, and the size is the length.

type Counts = { Lines: int; Words: int; Bytes: int }

let isSeparator (b: byte) =
    b = 32uy || b = 9uy || b = 10uy || b = 13uy || b = 11uy || b = 12uy

let count (raw: byte[]) =
    let mutable lines = 0
    let mutable words = 0
    let mutable inWord = false
    for b in raw do
        if b = 10uy then lines <- lines + 1
        if isSeparator b then
            inWord <- false
        else if not inWord then
            words <- words + 1
            inWord <- true
    { Lines = lines; Words = words; Bytes = raw.Length }
