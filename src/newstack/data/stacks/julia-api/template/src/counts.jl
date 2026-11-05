"""A `wc`-shaped count of one piece of text."""
struct Counts
    lines::Int
    words::Int
    bytes::Int
end

"""
    count_text(text) -> Counts

Count the text the way `wc` does: a line ends at a `\\n`, a word is a maximal
run of characters that are not whitespace, and bytes are the UTF-8 encoding.

`ncodeunits` is the number of bytes in the string's UTF-8 encoding, which is
why `"héllo"` reports 6 bytes while `length` would report 5 characters. The
word scan is written out by hand because `length` is not defined for the
iterator `eachmatch` returns.
"""
function count_text(text::AbstractString)::Counts
    lines = 0
    words = 0
    in_word = false
    for character in text
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
    Counts(lines, words, ncodeunits(text))
end
