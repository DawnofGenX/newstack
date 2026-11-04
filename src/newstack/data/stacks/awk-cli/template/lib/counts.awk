# Counting over bytes. The caller must run awk in the C locale, where length()
# counts bytes rather than characters, so a multi-byte character counts as
# several bytes exactly like wc does.

# Sets COUNT_LINES, COUNT_WORDS and COUNT_BYTES for `text`.
function counts_of(text,   copy) {
    COUNT_BYTES = length(text)

    copy = text
    COUNT_LINES = gsub(/\n/, "&", copy)

    copy = text
    COUNT_WORDS = gsub(/[^ \t\n\r\v\f]+/, "&", copy)
}

function figure_of(which) {
    if (which == "lines") {
        return COUNT_LINES
    }
    if (which == "words") {
        return COUNT_WORDS
    }
    return COUNT_BYTES
}
