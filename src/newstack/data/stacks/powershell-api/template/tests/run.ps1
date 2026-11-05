# A plain assertion script: no test framework to install, and it exits 1 the
# moment one check disagrees.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot '..' 'src' 'Textstat.psm1') -Force

$script:checks = 0
$script:failed = 0

function Assert-Equal {
    param($Expected, $Actual, [string]$Name)
    $script:checks++
    if ("$Expected" -eq "$Actual") {
        Write-Host "ok   $Name"
    } else {
        $script:failed++
        Write-Host "FAIL $Name (expected [$Expected], got [$Actual])"
    }
}

function Get-CountsText { param([string]$Text) (Get-TextstatCounts -Text $Text) }

Assert-Equal 1 (Get-CountsText "hello world`n").lines 'counts newline terminators'
Assert-Equal 2 (Get-CountsText "hello world`n").words 'counts whitespace separated words'
Assert-Equal 12 (Get-CountsText "hello world`n").bytes 'counts bytes, not characters'
Assert-Equal 0 (Get-CountsText '').lines 'empty input has no lines'
Assert-Equal 0 (Get-CountsText '').words 'empty input has no words'
Assert-Equal 0 (Get-CountsText '').bytes 'empty input has no bytes'
Assert-Equal 0 (Get-CountsText 'abc').lines 'an unterminated last line is not counted'
Assert-Equal 1 (Get-CountsText 'abc').words 'an unterminated word is still a word'
Assert-Equal 3 (Get-CountsText "`n`nx`n").lines 'blank lines count'
Assert-Equal 4 (Get-CountsText "  `t ").bytes 'whitespace bytes are raw bytes'
Assert-Equal 0 (Get-CountsText "  `t ").words 'runs of whitespace are not words'
Assert-Equal 14 (Get-CountsText "héllo wörld`n").bytes 'a multi-byte string counts its UTF-8 bytes'
Assert-Equal 2 (Get-CountsText "héllo wörld`n").words 'a multi-byte string counts one word per run'
Assert-Equal 5 (Get-CountsText "🙂`n").bytes 'an emoji is four bytes'

$health = Invoke-TextstatRoute -Method 'GET' -Path '/health'
Assert-Equal 200 $health.status 'GET /health is 200'
Assert-Equal '{"status":"ok"}' $health.body 'GET /health answers a status object'

$stats = Invoke-TextstatRoute -Method 'GET' -Path '/stats' -Query '?text=hello%20world%0A'
Assert-Equal 200 $stats.status 'GET /stats is 200'
Assert-Equal '{"text":"hello world\n","lines":1,"words":2,"bytes":12}' $stats.body 'GET /stats counts the decoded query value'

$missing = Invoke-TextstatRoute -Method 'GET' -Path '/stats'
Assert-Equal 422 $missing.status 'GET /stats without text is 422'
Assert-Equal '{"error":"missing_text"}' $missing.body 'GET /stats without text names the field'

$posted = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '{"text":"a b\nc\n"}'
Assert-Equal 200 $posted.status 'POST /stats is 200'
Assert-Equal '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' $posted.body 'POST /stats counts the posted text'

$padded = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '{"text":"  padded  \n"}'
Assert-Equal '{"text":"  padded  \n","lines":1,"words":1,"bytes":11}' $padded.body 'the text is echoed exactly as sent'

$numeric = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '{"text":42}'
Assert-Equal 422 $numeric.status 'a numeric text is 422'
Assert-Equal '{"error":"missing_text"}' $numeric.body 'a numeric text is missing_text'

$quoted = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '{"text":"42"}'
Assert-Equal 200 $quoted.status 'a quoted number is a string'

$empty = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '{}'
Assert-Equal '{"error":"missing_text"}' $empty.body 'an object without text is missing_text'

$broken = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body 'nope'
Assert-Equal '{"error":"invalid_json"}' $broken.body 'a broken body is invalid_json'

$array = Invoke-TextstatRoute -Method 'POST' -Path '/stats' -Body '[1,2]'
Assert-Equal '{"error":"invalid_json"}' $array.body 'a JSON array is not an object'

$wrong = Invoke-TextstatRoute -Method 'DELETE' -Path '/health'
Assert-Equal 405 $wrong.status 'a known path with another method is 405'
Assert-Equal '{"error":"method_not_allowed"}' $wrong.body 'the 405 names itself'

$gone = Invoke-TextstatRoute -Method 'GET' -Path '/nope'
Assert-Equal 404 $gone.status 'an unknown route is 404'
Assert-Equal '{"error":"not_found","detail":"no route for GET /nope"}' $gone.body 'the 404 carries a detail'

$utf8 = Invoke-TextstatRoute -Method 'GET' -Path '/stats' -Query 'text=h%C3%A9llo%20w%C3%B6rld%0A'
Assert-Equal 14 ($utf8.body | ConvertFrom-Json).bytes 'percent-encoded UTF-8 is counted in bytes'

Write-Host ""
if ($script:failed -gt 0) {
    Write-Host "$($script:failed) of $($script:checks) checks failed"
    exit 1
}
Write-Host "$($script:checks) checks passed"
