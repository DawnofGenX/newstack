$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../lib/HashCli.ps1"
$passed = 0; $failed = 0
function Check($name, $ok) { if ($ok) { $script:passed++ } else { $script:failed++; Write-Host "FAIL $name" } }

$tmp = New-TemporaryFile
Set-Content -Path $tmp.FullName -Value 'abc' -NoNewline
$hash256 = Get-FileHashString -Path $tmp.FullName -Algorithm SHA256
Check 'hash length' ($hash256.Length -eq 64)
Invoke-HashCli -Arguments @('verify', $tmp.FullName, $hash256) | Out-Null
Check 'verify file ok' ($global:HashCliExitCode -eq 0)
Invoke-HashCli -Arguments @('verify', $tmp.FullName, '0') | Out-Null
Check 'verify file bad' ($global:HashCliExitCode -eq 1)

$dir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ([guid]::NewGuid()))
Set-Content -Path (Join-Path $dir.FullName 'a.txt') -Value 'x' -NoNewline
$manifest = Invoke-HashCli -Arguments @('manifest', $dir.FullName)
$manFile = Join-Path $dir.FullName 'manifest.txt'
Set-Content -Path $manFile -Value $manifest
Invoke-HashCli -Arguments @('verify-manifest', $manFile, $dir.FullName) | Out-Null
Check 'manifest verify ok' ($global:HashCliExitCode -eq 0)

Remove-Item $tmp.FullName -Force
Remove-Item $dir.FullName -Recurse -Force

Write-Host "checks: $($passed+$failed), passed: $passed, failed: $failed"
if ($failed -eq 0) { exit 0 } else { exit 1 }
