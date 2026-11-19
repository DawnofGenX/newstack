#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path (Split-Path -Parent $here) 'lib/EnvDiff.ps1')

$script:passed = 0
$script:failed = 0
function Check([string] $Name, [scriptblock] $Body) {
    try {
        if (& $Body) { $script:passed++ }
        else { Write-Host "FAIL $Name"; $script:failed++ }
    } catch { Write-Host "FAIL $Name : $_"; $script:failed++ }
}
$files = @{
    'left.env' = "A=1`nB=two # comment`n`nexport C=`"hello world`"`n"
    'right.env' = "A=1`nB=different`nD=4`n"
}
$reader = { param($path)
    if (-not $files.ContainsKey($path)) { throw "no such file: $path" }
    return $files[$path]
}
function Capture([string[]] $CliArgs) {
    $out = [System.IO.StringWriter]::new()
    $err = [System.IO.StringWriter]::new()
    $code = Invoke-EnvDiffCli -Arguments $CliArgs -ReadFile $reader -Out $out -Err $err
    return [pscustomobject]@{ Code = $code; Out = $out.ToString(); Err = $err.ToString() }
}

Check 'parse handles comments and export' {
    $v = Parse-DotEnv -Text ('A=1 # trail' + "`n" + 'export B="x y"')
    ($v['A'] -eq '1') -and ($v['B'] -eq 'x y')
}
Check 'parse rejects a malformed line' {
    $bad = $false
    try { Parse-DotEnv -Text 'NOEQUALS' } catch { $bad = ($_.Exception.Message -like 'line 1*') }
    $bad
}
Check 'compare classifies all four groups' {
    $d = Compare-Env -Left (Parse-DotEnv -Text ('A=1' + "`n" + 'B=2')) -Right (Parse-DotEnv -Text ('A=1' + "`n" + 'C=3'))
    ($d.Same -contains 'A') -and ($d.Removed -contains 'B') -and ($d.Added -contains 'C')
}
Check 'help exits zero' { (Capture @('--help')).Code -eq 0 }
Check 'usage error exits two' { (Capture @('only-one.env')).Code -eq 2 }
Check 'unknown option exits two' { (Capture @('--bogus')).Code -eq 2 }
Check 'missing file exits one' { (Capture @('nope.env', 'right.env')).Code -eq 1 }
Check 'text diff shows changed key' { (Capture @('left.env', 'right.env')).Out -match '~ B' }
Check 'json diff is valid and sorted' {
    $r = Capture @('--json', 'left.env', 'right.env')
    $o = $r.Out | ConvertFrom-Json
    ($r.Code -eq 0) -and ($o.added -join ',' -eq 'D') -and ($o.changed -join ',' -eq 'B')
}
Check 'quiet mode is terse' { (Capture @('--quiet', 'left.env', 'right.env')).Out.Trim() -eq 'differences: 3' }

Write-Host "checks: $($script:passed + $script:failed), passed: $script:passed, failed: $script:failed"
if ($script:failed -gt 0) { exit 1 }
exit 0
