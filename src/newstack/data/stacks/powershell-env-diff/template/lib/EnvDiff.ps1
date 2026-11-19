# Parse dotenv files and compute a structural diff. The core never touches
# the real filesystem: callers pass a reader scriptblock that maps a path to
# text, so the CLI and the tests share exactly the same code.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Parse-DotEnv {
    param([AllowEmptyString()][string] $Text)
    $values = [ordered]@{}
    $lineNo = 0
    foreach ($raw in ($Text -split "`r?`n")) {
        $lineNo++
        $line = $raw.Trim()
        if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
        if ($line.StartsWith('export ')) { $line = $line.Substring(7).Trim() }
        $eq = $line.IndexOf('=')
        if ($eq -lt 1) { throw "line $lineNo`: expected KEY=VALUE" }
        $key = $line.Substring(0, $eq).Trim()
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
            throw "line $lineNo`: invalid key '$key'"
        }
        $value = $line.Substring($eq + 1).Trim()
        if ($value.Length -ge 2) {
            $first = $value[0]
            if (($first -eq '"' -or $first -eq "'") -and $value[-1] -eq $first) {
                $value = $value.Substring(1, $value.Length - 2)
                if ($first -eq '"') { $value = $value -replace '\\n', "`n" -replace '\\t', "`t" }
            } else {
                $hash = $value.IndexOf(' #')
                if ($hash -ge 0) { $value = $value.Substring(0, $hash).TrimEnd() }
            }
        }
        $values[$key] = $value
    }
    return $values
}

function Compare-Env {
    param($Left, $Right)
    $added = @(); $removed = @(); $changed = @(); $same = @()
    foreach ($key in $Left.Keys) {
        if (-not $Right.Contains($key)) { $removed += $key }
        elseif ($Left[$key] -cne $Right[$key]) { $changed += $key }
        else { $same += $key }
    }
    foreach ($key in $Right.Keys) {
        if (-not $Left.Contains($key)) { $added += $key }
    }
    return [pscustomobject]@{
        Added = @($added | Sort-Object)
        Removed = @($removed | Sort-Object)
        Changed = @($changed | Sort-Object)
        Same = @($same | Sort-Object)
    }
}

function Format-EnvDiff {
    param($Diff, [switch] $Json, [switch] $Quiet)
    if ($Quiet) {
        $n = $Diff.Added.Count + $Diff.Removed.Count + $Diff.Changed.Count
        if ($n -gt 0) { return "differences: $n" } else { return 'identical' }
    }
    if ($Json) {
        return [pscustomobject]@{
            added = @($Diff.Added); removed = @($Diff.Removed)
            changed = @($Diff.Changed); same = @($Diff.Same)
        } | ConvertTo-Json -Compress
    }
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($key in $Diff.Added) { $lines.Add("+ $key") }
    foreach ($key in $Diff.Removed) { $lines.Add("- $key") }
    foreach ($key in $Diff.Changed) { $lines.Add("~ $key") }
    foreach ($key in $Diff.Same) { $lines.Add("  $key") }
    if ($lines.Count -eq 0) { $lines.Add('identical') }
    return ($lines -join "`n")
}

function Invoke-EnvDiffCli {
    param(
        [string[]] $Arguments,
        [scriptblock] $ReadFile,
        [System.IO.TextWriter] $Out,
        [System.IO.TextWriter] $Err
    )
    $json = $false; $quiet = $false; $paths = [System.Collections.Generic.List[string]]::new()
    foreach ($arg in $Arguments) {
        switch -Exact ($arg) {
            '--help' { $Out.WriteLine('Usage: {{ npm_name }} [--json] [--quiet] LEFT.env RIGHT.env'); return 0 }
            '--json' { $json = $true }
            '--quiet' { $quiet = $true }
            default {
                if ($arg.StartsWith('-')) {
                    $Err.WriteLine("unexpected option: $arg"); return 2
                }
                $paths.Add($arg)
            }
        }
    }
    if ($paths.Count -ne 2) {
        $Err.WriteLine('expected exactly two .env files'); return 2
    }
    try {
        $leftText = & $ReadFile $paths[0]
        $rightText = & $ReadFile $paths[1]
    } catch {
        $Err.WriteLine("error: $($_.Exception.Message)"); return 1
    }
    try {
        $left = Parse-DotEnv -Text $leftText
        $right = Parse-DotEnv -Text $rightText
        $diff = Compare-Env -Left $left -Right $right
        $Out.WriteLine((Format-EnvDiff -Diff $diff -Json:$json -Quiet:$quiet))
        return 0
    } catch {
        $Err.WriteLine("error: $($_.Exception.Message)"); return 1
    }
}
