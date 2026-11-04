Set-StrictMode -Version Latest

function Invoke-Runner {
    param([string[]]$Arguments, $Fake)

    return Invoke-TextStatRunner -Arguments $Arguments -Io $Fake.Hashtable -Program 'prog'
}

function Test-TextStatRunner {
    $fake = New-FakeIo -Files @{ 'a.txt' = (ConvertTo-Bytes "alpha beta`ngamma`n") }
    $code = Invoke-Runner -Arguments @('a.txt') -Fake $fake
    Check-Equal 'file exit code' 0 $code
    Check-Equal 'file row' " 2  3 17 a.txt`n" $fake.Out.ToString()

    $fake = New-FakeIo -Files @{ 'a.txt' = (ConvertTo-Bytes "alpha beta`ngamma`n") }
    $code = Invoke-Runner -Arguments @('-w', 'a.txt') -Fake $fake
    Check-Equal 'single figure exit code' 0 $code
    Check-Equal 'single figure row' "3 a.txt`n" $fake.Out.ToString()

    $fake = New-FakeIo -Files @{
        'a.txt' = (ConvertTo-Bytes "alpha beta`ngamma`n")
        'b.txt' = (ConvertTo-Bytes 'one line, no trailing newline')
    }
    $code = Invoke-Runner -Arguments @('a.txt', 'b.txt') -Fake $fake
    Check-Equal 'two files exit code' 0 $code
    Check-Equal 'two files rows' " 2  3 17 a.txt`n 0  5 29 b.txt`n 2  8 46 total`n" $fake.Out.ToString()

    $fake = New-FakeIo -Files @{ 'a.txt' = (ConvertTo-Bytes "alpha beta`ngamma`n") }
    $code = Invoke-Runner -Arguments @('a.txt', 'nope.txt') -Fake $fake
    Check-Equal 'missing file exit code' 1 $code
    Check-Equal 'missing file rows' " 2  3 17 a.txt`n 2  3 17 total`n" $fake.Out.ToString()
    Check-Equal 'missing file message' "prog: error: cannot open 'nope.txt'`n" $fake.Err.ToString()

    $fake = New-FakeIo -Stdin (ConvertTo-Bytes "alpha beta`ngamma`n") -Streaming $true
    $code = Invoke-Runner -Arguments @() -Fake $fake
    Check-Equal 'stdin exit code' 0 $code
    Check-Equal 'stdin row is padded and unlabelled' "      2       3      17`n" $fake.Out.ToString()

    $fake = New-FakeIo -Stdin (ConvertTo-Bytes "alpha beta`ngamma`n") -Streaming $true
    $code = Invoke-Runner -Arguments @('-w') -Fake $fake
    Check-Equal 'stdin single figure' "3`n" $fake.Out.ToString()

    $fake = New-FakeIo -Stdin (ConvertTo-Bytes "alpha beta`ngamma`n") -Streaming $true
    $code = Invoke-Runner -Arguments @('-w', '-') -Fake $fake
    Check-Equal 'explicit dash keeps its label' "3 -`n" $fake.Out.ToString()

    $fake = New-FakeIo -Stdin (ConvertTo-Bytes "alpha beta`ngamma`n")
    $code = Invoke-Runner -Arguments @('--help') -Fake $fake
    Check-Equal 'help exit code' 0 $code
    Check 'help mentions usage' ($fake.Out.ToString().StartsWith('Usage: prog'))

    $big = ConvertTo-Bytes ('x' * 120)
    $fake = New-FakeIo -Files @{ 'big.txt' = $big }
    $code = Invoke-Runner -Arguments @('big.txt') -Fake $fake
    Check-Equal 'width follows the byte count' "  0   1 120 big.txt`n" $fake.Out.ToString()

    $fake = New-FakeIo -Files @{ 'big.txt' = $big }
    $code = Invoke-Runner -Arguments @('-l', 'big.txt') -Fake $fake
    Check-Equal 'a single figure is never padded' "0 big.txt`n" $fake.Out.ToString()

    $fake = New-FakeIo
    $code = Invoke-Runner -Arguments @('--version') -Fake $fake
    Check-Equal 'version exit code' 0 $code
    Check-Equal 'version text' "prog 0.1.0`n" $fake.Out.ToString()

    $fake = New-FakeIo
    $code = Invoke-Runner -Arguments @('--bogus') -Fake $fake
    Check-Equal 'usage error exit code' 2 $code
    Check-Equal 'usage error text' "prog: unknown option: --bogus`nTry 'prog --help' for more information.`n" $fake.Err.ToString()
    Check-Equal 'usage error keeps stdout empty' '' $fake.Out.ToString()
}
