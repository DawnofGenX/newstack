# Socket glue only: one HttpListener, every decision taken by Invoke-TextstatRoute.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'Textstat.psm1') -Force

$port = if ($env:PORT) { [int]$env:PORT } else { 8080 }
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://127.0.0.1:$port/")
$listener.Start()
Write-Host "listening on http://127.0.0.1:$port"

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
    } catch {
        break
    }

    $request = $context.Request
    $body = ''
    if ($request.HasEntityBody) {
        $reader = [System.IO.StreamReader]::new($request.InputStream, $request.ContentEncoding)
        $body = $reader.ReadToEnd()
        $reader.Dispose()
    }

    $reply = Invoke-TextstatRoute -Method $request.HttpMethod -Path $request.Url.AbsolutePath -Query $request.Url.Query -Body $body

    $response = $context.Response
    $response.StatusCode = $reply.status
    $response.ContentType = 'application/json'
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($reply.body)
    $response.ContentLength64 = $bytes.Length
    $response.OutputStream.Write($bytes, 0, $bytes.Length)
    $response.OutputStream.Close()
}
