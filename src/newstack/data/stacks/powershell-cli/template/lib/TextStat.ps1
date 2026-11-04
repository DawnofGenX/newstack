Set-StrictMode -Version Latest

$script:TextStatVersion = '0.1.0'

function Test-TextStatSpace {
    param([int]$Byte)

    return ($Byte -eq 32 -or $Byte -eq 9 -or $Byte -eq 10 -or
        $Byte -eq 11 -or $Byte -eq 12 -or $Byte -eq 13)
}

function Get-TextStatCounts {
    param([AllowEmptyCollection()][byte[]]$Data)

    $lines = 0
    $words = 0
    $inWord = $false

    foreach ($byte in $Data) {
        if ($byte -eq 10) { $lines++ }

        if (Test-TextStatSpace -Byte $byte) {
            $inWord = $false
        }
        elseif (-not $inWord) {
            $words++
            $inWord = $true
        }
    }

    return [pscustomobject]@{
        Lines = $lines
        Words = $words
        Bytes = $Data.Length
    }
}

function Add-TextStatCounts {
    param($Left, $Right)

    return [pscustomobject]@{
        Lines = $Left.Lines + $Right.Lines
        Words = $Left.Words + $Right.Words
        Bytes = $Left.Bytes + $Right.Bytes
    }
}

function Format-TextStatRow {
    param([int[]]$Values, [int]$Width, [string]$Label)

    $cells = foreach ($value in $Values) { $value.ToString().PadLeft($Width) }
    $row = $cells -join ' '

    if ($Label) { return "$row $Label" }

    return $row
}

function Get-TextStatUsage {
    param([string]$Program)

    return @"
Usage: $Program [OPTION]... [FILE]...
Count lines, words, and bytes for each FILE.

  -l, --lines    print the newline count
  -w, --words    print the word count
  -c, --bytes    print the byte count
  -h, --help     show this message and exit
  -V, --version  print the version and exit

With no FILE, or when FILE is -, read standard input.
"@
}
