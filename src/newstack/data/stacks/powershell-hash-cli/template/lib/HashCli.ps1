
function Get-FileHashString {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$Algorithm = 'SHA256'
    )
    return (Get-FileHash -Path $Path -Algorithm $Algorithm).Hash.ToLowerInvariant()
}

function New-Manifest {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$Algorithm = 'SHA256'
    )
    $rootFull = (Resolve-Path $Root).Path
    $files = Get-ChildItem -Path $rootFull -Recurse -File | Sort-Object FullName
    $lines = foreach ($f in $files) {
        $rel = $f.FullName.Substring($rootFull.Length).TrimStart('\', '/') -replace '\\', '/'
        $h = Get-FileHashString -Path $f.FullName -Algorithm $Algorithm
        "$h  $rel"
    }
    return ($lines -join [Environment]::NewLine)
}

function Test-Manifest {
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [string]$Root = '.',
        [string]$Algorithm = 'SHA256'
    )
    $rootFull = (Resolve-Path $Root).Path
    $ok = $true
    foreach ($line in (Get-Content -Path $ManifestPath)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split '\s+', 2
        if ($parts.Count -lt 2) { $ok = $false; continue }
        $expected = $parts[0].ToLowerInvariant()
        $rel = $parts[1]
        $path = Join-Path $rootFull $rel
        if (-not (Test-Path -Path $path)) {
            $ok = $false
            Write-Host "missing: $rel"
            continue
        }
        $actual = Get-FileHashString -Path $path -Algorithm $Algorithm
        if ($actual -ne $expected) {
            $ok = $false
            Write-Host "mismatch: $rel"
        }
    }
    return $ok
}

function Show-Usage {
    param([string]$Program = 'hash-cli')
    Write-Output "Usage: $Program <command> [args]"
    Write-Output "Commands:"
    Write-Output "  hash FILE [SHA256|SHA512]"
    Write-Output "  verify FILE EXPECTED [SHA256|SHA512]"
    Write-Output "  verify-manifest MANIFEST [ROOT] [SHA256|SHA512]"
    Write-Output "  manifest ROOT [SHA256|SHA512]"
}

function Invoke-HashCli {
    param([string[]]$Arguments)
    if (-not $Arguments -or $Arguments.Count -eq 0) {
        Show-Usage
        $global:HashCliExitCode = 2
        return
    }
    $cmd = $Arguments[0].ToLowerInvariant()
    switch ($cmd) {
        'hash' {
            if ($Arguments.Count -lt 2) { Show-Usage; $global:HashCliExitCode = 2; return }
            $algo = if ($Arguments.Count -ge 3) { $Arguments[2] } else { 'SHA256' }
            Write-Output (Get-FileHashString -Path $Arguments[1] -Algorithm $algo)
            $global:HashCliExitCode = 0
            return
        }
        'verify-manifest' {
            if ($Arguments.Count -lt 2) { Show-Usage; $global:HashCliExitCode = 2; return }
            $manifest = $Arguments[1]
            $root = '.'
            $algo = 'SHA256'
            if ($Arguments.Count -ge 3) { $root = $Arguments[2] }
            if ($Arguments.Count -ge 4) { $algo = $Arguments[3] }
            if (Test-Manifest -ManifestPath $manifest -Root $root -Algorithm $algo) { $global:HashCliExitCode = 0 } else { $global:HashCliExitCode = 1 }
            return
        }
        'verify' {
            if ($Arguments.Count -lt 3) { Show-Usage; $global:HashCliExitCode = 2; return }
            $file = $Arguments[1]
            $expected = $Arguments[2].ToLowerInvariant()
            $algo = if ($Arguments.Count -ge 4) { $Arguments[3] } else { 'SHA256' }
            $actual = Get-FileHashString -Path $file -Algorithm $algo
            if ($actual -eq $expected) { $global:HashCliExitCode = 0 } else { Write-Host 'mismatch'; $global:HashCliExitCode = 1 }
            return
        }
        'manifest' {
            if ($Arguments.Count -lt 2) { Show-Usage; $global:HashCliExitCode = 2; return }
            $algo = if ($Arguments.Count -ge 3) { $Arguments[2] } else { 'SHA256' }
            Write-Output (New-Manifest -Root $Arguments[1] -Algorithm $algo)
            $global:HashCliExitCode = 0
            return
        }
        '--help' { Show-Usage; $global:HashCliExitCode = 0; return }
        '-h' { Show-Usage; $global:HashCliExitCode = 0; return }
        default { Show-Usage; $global:HashCliExitCode = 2; return }
    }
}
