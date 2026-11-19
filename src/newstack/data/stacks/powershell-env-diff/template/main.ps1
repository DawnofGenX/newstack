#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'lib/EnvDiff.ps1')
$reader = { param($path) Get-Content -LiteralPath $path -Raw }
exit (Invoke-EnvDiffCli -Arguments @($args) -ReadFile $reader -Out ([Console]::Out) -Err ([Console]::Error))
