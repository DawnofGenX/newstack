Set-StrictMode -Version Latest
. "$PSScriptRoot/lib/HashCli.ps1"
$global:HashCliExitCode = 0
Invoke-HashCli -Arguments $args
exit $global:HashCliExitCode
