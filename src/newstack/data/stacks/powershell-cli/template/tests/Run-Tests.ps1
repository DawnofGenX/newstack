Set-StrictMode -Version Latest

. "$PSScriptRoot/../lib/TextStat.ps1"
. "$PSScriptRoot/../lib/Options.ps1"
. "$PSScriptRoot/../lib/Runner.ps1"
. "$PSScriptRoot/Harness.ps1"
. "$PSScriptRoot/Counts.Tests.ps1"
. "$PSScriptRoot/Options.Tests.ps1"
. "$PSScriptRoot/Runner.Tests.ps1"

Test-TextStatCounts
Test-TextStatOptions
Test-TextStatRunner

$summary = Get-HarnessSummary
Write-Host "$($summary.Passed) passed, $($summary.Failed) failed."

if ($summary.Failed -gt 0) { exit 1 }

exit 0
