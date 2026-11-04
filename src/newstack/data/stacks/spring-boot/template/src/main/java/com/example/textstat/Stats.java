package com.example.textstat;

/** Immutable wc-style counts: lines, words and bytes. */
public record Stats(long lines, long words, long bytes) {
}
