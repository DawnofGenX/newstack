namespace {{ package_name }};

/// <summary>Line, word and byte counts for a piece of text.</summary>
public readonly record struct Counts(int Lines, int Words, int Bytes);
