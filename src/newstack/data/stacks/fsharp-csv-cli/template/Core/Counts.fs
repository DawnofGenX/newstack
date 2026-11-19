namespace {{ package_name }}

open System
open System.Text

/// <summary>Line, word and byte totals for one piece of text.</summary>
type Counts =
    { Lines: int64
      Words: int64
      Bytes: int64 }

/// <summary>Pure counting logic, with no I/O so tests drive it directly.</summary>
[<RequireQualifiedAccess>]
module Counts =

    /// <summary>The empty total, which is where a multi-file sum starts.</summary>
    let zero = { Lines = 0L; Words = 0L; Bytes = 0L }

    /// <summary>Adds two sets of figures, which is how a multi-file total is built.</summary>
    let plus (left: Counts) (right: Counts) : Counts =
        { Lines = left.Lines + right.Lines
          Words = left.Words + right.Words
          Bytes = left.Bytes + right.Bytes }

    /// <summary>
    /// Counts lines and words in <paramref name="text"/>, using a byte count the
    /// caller already knows (the raw file length, which need not be UTF-8 length).
    /// A line is counted when a newline closes it, so a final unterminated line is
    /// not one; a word is a run of non-whitespace characters.
    /// </summary>
    let ofStringWithBytes (bytes: int64) (text: string) : Counts =
        let lines, words, _ =
            text.ToCharArray()
            |> Array.fold
                (fun (lines, words, inWord) current ->
                    let lineCount = if current = '\n' then lines + 1L else lines
                    if Char.IsWhiteSpace current then
                        lineCount, words, false
                    elif inWord then
                        lineCount, words, true
                    else
                        lineCount, words + 1L, true)
                (0L, 0L, false)

        { Lines = lines; Words = words; Bytes = bytes }

    /// <summary>Counts the UTF-8 encoding of <paramref name="text"/>.</summary>
    let ofString (text: string) : Counts =
        ofStringWithBytes (int64 (Encoding.UTF8.GetByteCount text)) text

    /// <summary>Counts the raw bytes, decoding them as UTF-8 for lines and words.</summary>
    let ofBytes (data: byte[]) : Counts =
        ofStringWithBytes (int64 data.Length) (Encoding.UTF8.GetString data)
