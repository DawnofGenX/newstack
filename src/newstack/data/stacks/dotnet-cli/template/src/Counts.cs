namespace {{ package_name }};

/// <summary>Line, word and byte totals for one piece of text.</summary>
public readonly record struct Counts(long Lines, long Words, long Bytes)
{
    /// <summary>Adds two sets of figures, which is how a multi-file total is built.</summary>
    public Counts Plus(Counts other) =>
        new(Lines + other.Lines, Words + other.Words, Bytes + other.Bytes);
}
