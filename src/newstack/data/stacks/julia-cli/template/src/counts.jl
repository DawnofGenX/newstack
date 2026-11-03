"""
    Counts

Line, word and byte totals for one input. A value type, so two totals with the
same numbers are equal and tests can compare against a literal.
"""
struct Counts
    lines::Int
    words::Int
    bytes::Int
end

function Base.:(==)(left::Counts, right::Counts)
    return left.lines == right.lines &&
           left.words == right.words &&
           left.bytes == right.bytes
end

Base.hash(counts::Counts, h::UInt) = hash(counts.words, hash(counts.lines, hash(counts.bytes, h)))

"""
    Base.:+(left::Counts, right::Counts) -> Counts

Adds two totals componentwise, so several files can be reported as one.
"""
function Base.:+(left::Counts, right::Counts)
    return Counts(
        left.lines + right.lines,
        left.words + right.words,
        left.bytes + right.bytes,
    )
end

"""
    counts(data::AbstractString) -> Counts

Count newlines, runs of non-whitespace and raw bytes in *data*.

No I/O and no printing: the caller decides where the text came from and where
the figures go. Lines follow `wc -l` (a trailing newline terminates the line it
ends; an unterminated last line is not counted), words are maximal runs of
non-whitespace, and bytes are code units, so UTF-8 text counts what `wc -c`
counts.
"""
function counts(data::AbstractString)
    lines = 0
    words = 0
    in_word = false

    for character in data
        if character == '\n'
            lines += 1
        end
        if isspace(character)
            in_word = false
        elseif !in_word
            words += 1
            in_word = true
        end
    end

    return Counts(lines, words, ncodeunits(data))
end
