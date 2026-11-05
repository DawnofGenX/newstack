# Counting rules and the whole route table. Nothing here opens a socket, so the
# test script can pin every status code without a port.
Set-StrictMode -Version Latest

function Get-TextstatCounts {
    param([string]$Text)

    $characters = $Text.ToCharArray()
    $lines = 0
    $words = 0
    $inWord = $false
    foreach ($character in $characters) {
        if ($character -eq "`n") { $lines++ }
        if ([char]::IsWhiteSpace($character)) {
            $inWord = $false
        } elseif (-not $inWord) {
            $words++
            $inWord = $true
        }
    }

    [pscustomobject]@{
        lines = $lines
        words = $words
        bytes = [text.encoding]::UTF8.GetByteCount($Text)
    }
}

function ConvertTo-TextstatJson {
    param([System.Collections.IDictionary]$Value)
    # ConvertTo-Json keeps the insertion order of an ordered dictionary, so the
    # wire format is stable and a grep in the verify step can look for one key.
    $ordered = [ordered]@{}
    foreach ($key in $Value.Keys) { $ordered[$key] = $Value[$key] }
    ConvertTo-Json -InputObject $ordered -Compress -Depth 6
}

function New-TextstatReply {
    param([int]$Status, [System.Collections.IDictionary]$Body)
    [pscustomobject]@{ status = $Status; body = (ConvertTo-TextstatJson $Body) }
}

function Get-TextstatQueryValue {
    param([string]$Query, [string]$Name)

    $trimmed = $Query.TrimStart('?')
    if ([string]::IsNullOrEmpty($trimmed)) { return $null }
    foreach ($pair in $trimmed.Split('&')) {
        if ([string]::IsNullOrEmpty($pair)) { continue }
        $parts = $pair.Split('=', 2)
        if ($parts[0] -eq $Name) {
            $raw = if ($parts.Length -gt 1) { $parts[1] } else { '' }
            return [uri]::UnescapeDataString($raw.Replace('+', ' '))
        }
    }
    return $null
}

function Get-TextstatBodyText {
    param([string]$Body)
    # Three outcomes: a string, a non-string, or not JSON at all.
    try {
        $parsed = ConvertFrom-Json -InputObject $Body -ErrorAction Stop
    } catch {
        return @{ kind = 'invalid' }
    }
    if ($null -eq $parsed -or $parsed -isnot [pscustomobject]) { return @{ kind = 'invalid' } }
    $property = $parsed.PSObject.Properties['text']
    if ($null -eq $property) { return @{ kind = 'missing' } }
    if ($property.Value -is [string]) { return @{ kind = 'text'; text = $property.Value } }
    return @{ kind = 'missing' }
}

function Invoke-TextstatRoute {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Query = '',
        [string]$Body = ''
    )

    $method = $Method.ToUpperInvariant()

    if ($method -eq 'GET' -and $Path -eq '/health') {
        return New-TextstatReply 200 ([ordered]@{ status = 'ok' })
    }
    if ($method -eq 'GET' -and $Path -eq '/stats') {
        $text = Get-TextstatQueryValue -Query $Query -Name 'text'
        if ($null -eq $text) { return New-TextstatReply 422 ([ordered]@{ error = 'missing_text' }) }
        $counts = Get-TextstatCounts -Text $text
        return New-TextstatReply 200 ([ordered]@{ text = $text; lines = $counts.lines; words = $counts.words; bytes = $counts.bytes })
    }
    if ($method -eq 'POST' -and $Path -eq '/stats') {
        $parsed = Get-TextstatBodyText -Body $Body
        if ($parsed.kind -eq 'invalid') { return New-TextstatReply 422 ([ordered]@{ error = 'invalid_json' }) }
        if ($parsed.kind -eq 'missing') { return New-TextstatReply 422 ([ordered]@{ error = 'missing_text' }) }
        $counts = Get-TextstatCounts -Text $parsed.text
        return New-TextstatReply 200 ([ordered]@{ text = $parsed.text; lines = $counts.lines; words = $counts.words; bytes = $counts.bytes })
    }
    if ($Path -eq '/health' -or $Path -eq '/stats') {
        return New-TextstatReply 405 ([ordered]@{ error = 'method_not_allowed' })
    }
    New-TextstatReply 404 ([ordered]@{ error = 'not_found'; detail = "no route for $method $Path" })
}

Export-ModuleMember -Function Get-TextstatCounts, Invoke-TextstatRoute, ConvertTo-TextstatJson
