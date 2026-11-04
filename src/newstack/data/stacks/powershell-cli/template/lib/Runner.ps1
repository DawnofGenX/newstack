Set-StrictMode -Version Latest

function Get-TextStatFigures {
    param($Options)

    $figures = New-Object System.Collections.Generic.List[string]
    if ($Options.Lines) { $figures.Add('Lines') }
    if ($Options.Words) { $figures.Add('Words') }
    if ($Options.Bytes) { $figures.Add('Bytes') }

    return $figures.ToArray()
}

function Invoke-TextStatRunner {
    param(
        [AllowEmptyCollection()][string[]]$Arguments,
        [hashtable]$Io,
        [string]$Program = 'textstat'
    )

    $options = ConvertFrom-TextStatArgs -Arguments $Arguments

    switch ($options.Status) {
        'Help' {
            $Io.Out.Write((Get-TextStatUsage -Program $Program))
            return 0
        }
        'Version' {
            $Io.Out.Write("$Program $script:TextStatVersion`n")
            return 0
        }
        'UsageError' {
            $Io.Err.Write("${Program}: unknown option: $($options.Message)`n")
            $Io.Err.Write("Try '$Program --help' for more information.`n")
            return 2
        }
    }

    [string[]]$figures = @(Get-TextStatFigures -Options $options)
    [string[]]$files = @($options.Files)
    [string[]]$operands = $files
    $implicit = $files.Count -eq 0
    if ($implicit) { $operands = @('-') }

    $rows = New-Object System.Collections.Generic.List[object]
    $total = $null
    $failed = $false
    $streamSeen = $false
    $operandCount = $operands.Count

    foreach ($operand in $operands) {
        if ($operand -eq '-') {
            if ((& $Io.IsStream)) { $streamSeen = $true }
            $counts = Get-TextStatCounts -Data (& $Io.ReadStdin)
            $label = if ($implicit) { '' } else { '-' }
        }
        else {
            $data = (& $Io.ReadAllBytes $operand)
            if ($null -eq $data) {
                $Io.Err.Write("${Program}: error: cannot open '$operand'`n")
                $failed = $true
                continue
            }
            $counts = Get-TextStatCounts -Data ([byte[]]$data)
            $label = $operand
        }

        $rows.Add([pscustomobject]@{ Counts = $counts; Label = $label })
        $total = if ($null -eq $total) { $counts } else { Add-TextStatCounts -Left $total -Right $counts }
    }

    $width = 1
    if ($figures.Count -ge 2) {
        if ($streamSeen) {
            $width = 7
        }
        elseif ($null -ne $total) {
            $width = $total.Bytes.ToString().Length
        }
    }

    foreach ($row in $rows) {
        $values = foreach ($figure in $figures) { $row.Counts.$figure }
        $Io.Out.Write((Format-TextStatRow -Values $values -Width $width -Label $row.Label) + "`n")
    }

    if ($operandCount -gt 1 -and $null -ne $total) {
        $values = foreach ($figure in $figures) { $total.$figure }
        $Io.Out.Write((Format-TextStatRow -Values $values -Width $width -Label 'total') + "`n")
    }

    if ($failed) { return 1 }

    return 0
}
