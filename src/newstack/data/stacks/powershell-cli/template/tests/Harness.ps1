Set-StrictMode -Version Latest

$script:Passed = 0
$script:Failed = 0
$script:Failures = New-Object System.Collections.Generic.List[string]

function Check {
    param([string]$Name, [bool]$Condition)

    if ($Condition) {
        $script:Passed++
    }
    else {
        $script:Failed++
        $script:Failures.Add($Name)
        Write-Host "FAIL $Name"
    }
}

function Check-Equal {
    param([string]$Name, $Expected, $Actual)

    if ([string]$Expected -ceq [string]$Actual) {
        $script:Passed++
    }
    else {
        $script:Failed++
        $script:Failures.Add($Name)
        Write-Host "FAIL $Name"
        Write-Host "  expected: [$Expected]"
        Write-Host "  actual:   [$Actual]"
    }
}

function Get-HarnessSummary {
    return [pscustomobject]@{
        Passed = $script:Passed
        Failed = $script:Failed
        Failures = $script:Failures.ToArray()
    }
}

function New-FakeIo {
    param(
        [hashtable]$Files = @{},
        [byte[]]$Stdin = @(),
        [bool]$Streaming = $false
    )

    $state = @{ In = $Stdin; Out = (New-Object System.IO.StringWriter); Err = (New-Object System.IO.StringWriter) }

    return [pscustomobject]@{
        Out = $state.Out
        Err = $state.Err
        Hashtable = @{
            ReadAllBytes = { param([string]$Path) if ($Files.ContainsKey($Path)) { , [byte[]]$Files[$Path] } else { $null } }.GetNewClosure()
            ReadStdin = { , [byte[]]$state.In }.GetNewClosure()
            IsStream = { $Streaming }.GetNewClosure()
            Out = $state.Out
            Err = $state.Err
        }
    }
}

function ConvertTo-Bytes {
    param([string]$Text)

    return , [System.Text.Encoding]::UTF8.GetBytes($Text)
}
