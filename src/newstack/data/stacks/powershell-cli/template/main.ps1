Set-StrictMode -Version Latest

. "$PSScriptRoot/lib/TextStat.ps1"
. "$PSScriptRoot/lib/Options.ps1"
. "$PSScriptRoot/lib/Runner.ps1"

function Read-AllBytes {
    param([string]$Path)

    try {
        return , [System.IO.File]::ReadAllBytes($Path)
    }
    catch {
        return $null
    }
}

function Test-StdinIsStream {
    try {
        $kind = (& stat -L -c %F /proc/self/fd/0 2>$null)
    }
    catch {
        return $true
    }

    return -not ($kind -eq 'regular file')
}

function Read-Stdin {
    $stream = [Console]::OpenStandardInput()
    $buffer = New-Object System.IO.MemoryStream
    $stream.CopyTo($buffer)

    return , $buffer.ToArray()
}

$io = @{
    ReadAllBytes = { param([string]$Path) Read-AllBytes -Path $Path }
    ReadStdin = { Read-Stdin }
    IsStream = { Test-StdinIsStream }
    Out = [Console]::Out
    Err = [Console]::Error
}

$code = Invoke-TextStatRunner -Arguments $args -Io $io -Program '{{ npm_name }}'
exit $code
