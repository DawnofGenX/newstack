Set-StrictMode -Version Latest

function New-TextStatOptions {
    param(
        [bool]$Lines = $false,
        [bool]$Words = $false,
        [bool]$Bytes = $false,
        [string[]]$Files = @(),
        [string]$Status = 'Ok',
        [string]$Message = ''
    )

    return [pscustomobject]@{
        Lines = $Lines
        Words = $Words
        Bytes = $Bytes
        Files = $Files
        Status = $Status
        Message = $Message
    }
}

function ConvertFrom-TextStatArgs {
    param([AllowEmptyCollection()][string[]]$Arguments)

    $lines = $false
    $words = $false
    $bytes = $false
    $chosen = $false
    $files = New-Object System.Collections.Generic.List[string]
    $help = $false
    $version = $false
    $literal = $false

    foreach ($argument in $Arguments) {
        if ($literal) {
            $files.Add($argument)
            continue
        }

        if ($argument -eq '--') {
            $literal = $true
            continue
        }

        if ($argument -eq '-') {
            $files.Add($argument)
            continue
        }

        if ($argument.StartsWith('--')) {
            switch ($argument) {
                '--help' { $help = $true }
                '--version' { $version = $true }
                '--lines' { $lines = $true; $chosen = $true }
                '--words' { $words = $true; $chosen = $true }
                '--bytes' { $bytes = $true; $chosen = $true }
                default {
                    return New-TextStatOptions -Status 'UsageError' -Message $argument
                }
            }
            continue
        }

        if ($argument.StartsWith('-') -and $argument.Length -gt 1) {
            foreach ($letter in $argument.Substring(1).ToCharArray()) {
                switch -CaseSensitive ([string]$letter) {
                    'l' { $lines = $true; $chosen = $true }
                    'w' { $words = $true; $chosen = $true }
                    'c' { $bytes = $true; $chosen = $true }
                    'h' { $help = $true }
                    'V' { $version = $true }
                    default {
                        return New-TextStatOptions -Status 'UsageError' -Message "-$letter"
                    }
                }
            }
            continue
        }

        $files.Add($argument)
    }

    if ($help) { return New-TextStatOptions -Status 'Help' }
    if ($version) { return New-TextStatOptions -Status 'Version' }

    if (-not $chosen) {
        $lines = $true
        $words = $true
        $bytes = $true
    }

    return New-TextStatOptions -Lines $lines -Words $words -Bytes $bytes -Files $files.ToArray()
}
