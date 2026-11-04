Set-StrictMode -Version Latest

function Test-TextStatCounts {
    $counts = Get-TextStatCounts -Data (ConvertTo-Bytes "alpha beta`ngamma`n")
    Check-Equal 'plain lines' 2 $counts.Lines
    Check-Equal 'plain words' 3 $counts.Words
    Check-Equal 'plain bytes' 17 $counts.Bytes

    $counts = Get-TextStatCounts -Data (ConvertTo-Bytes 'no trailing newline')
    Check-Equal 'no newline lines' 0 $counts.Lines
    Check-Equal 'no newline words' 3 $counts.Words
    Check-Equal 'no newline bytes' 19 $counts.Bytes

    $counts = Get-TextStatCounts -Data ([byte[]]@())
    Check-Equal 'empty lines' 0 $counts.Lines
    Check-Equal 'empty words' 0 $counts.Words
    Check-Equal 'empty bytes' 0 $counts.Bytes

    $counts = Get-TextStatCounts -Data (ConvertTo-Bytes "one`ttwo`vthree`ffour ")
    Check-Equal 'separators words' 4 $counts.Words
    Check-Equal 'separators bytes' 19 $counts.Bytes

    $counts = Get-TextStatCounts -Data ([byte[]](0x68, 0xC3, 0xA9, 0x6C, 0x6C, 0x6F, 0x20, 0x77, 0x6F, 0x72, 0x6C, 0x64, 0x0A))
    Check-Equal 'utf8 words' 2 $counts.Words
    Check-Equal 'utf8 bytes' 13 $counts.Bytes

    $sum = Add-TextStatCounts -Left (Get-TextStatCounts -Data (ConvertTo-Bytes "a`n")) -Right (Get-TextStatCounts -Data (ConvertTo-Bytes 'b'))
    Check-Equal 'sum lines' 1 $sum.Lines
    Check-Equal 'sum words' 2 $sum.Words
    Check-Equal 'sum bytes' 3 $sum.Bytes

    Check-Equal 'row pads to width' ' 2  3 17 a.txt' (Format-TextStatRow -Values @(2, 3, 17) -Width 2 -Label 'a.txt')
    Check-Equal 'row without label' '7' (Format-TextStatRow -Values @(7) -Width 1 -Label '')
}
