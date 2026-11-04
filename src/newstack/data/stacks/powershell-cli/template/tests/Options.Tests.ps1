Set-StrictMode -Version Latest

function Test-TextStatOptions {
    $options = ConvertFrom-TextStatArgs -Arguments @('a.txt')
    Check-Equal 'plain files' 'a.txt' ($options.Files -join ',')
    Check 'plain figures' ($options.Lines -and $options.Words -and $options.Bytes)
    Check-Equal 'plain status' 'Ok' $options.Status

    $options = ConvertFrom-TextStatArgs -Arguments @('-l')
    Check 'short lines' ($options.Lines -and -not $options.Words -and -not $options.Bytes)

    $options = ConvertFrom-TextStatArgs -Arguments @('-lw')
    Check 'cluster lines and words' ($options.Lines -and $options.Words -and -not $options.Bytes)

    $options = ConvertFrom-TextStatArgs -Arguments @('--bytes')
    Check 'long bytes' ($options.Bytes -and -not $options.Lines)

    $options = ConvertFrom-TextStatArgs -Arguments @('--', '-l')
    Check-Equal 'terminator keeps a flag-looking file' '-l' ($options.Files -join ',')
    Check 'terminator still counts all figures' ($options.Lines -and $options.Words -and $options.Bytes)

    $options = ConvertFrom-TextStatArgs -Arguments @('-')
    Check-Equal 'dash is an operand' '-' ($options.Files -join ',')

    $options = ConvertFrom-TextStatArgs -Arguments @('-h')
    Check-Equal 'short help' 'Help' $options.Status

    $options = ConvertFrom-TextStatArgs -Arguments @('--version')
    Check-Equal 'long version' 'Version' $options.Status

    $options = ConvertFrom-TextStatArgs -Arguments @('--bogus')
    Check-Equal 'unknown long option' 'UsageError' $options.Status
    Check-Equal 'unknown long option message' '--bogus' $options.Message

    $options = ConvertFrom-TextStatArgs -Arguments @('-lq')
    Check-Equal 'unknown short option' 'UsageError' $options.Status
    Check-Equal 'unknown short option message' '-q' $options.Message

    $options = ConvertFrom-TextStatArgs -Arguments @()
    Check 'no arguments count everything' ($options.Lines -and $options.Words -and $options.Bytes)
    Check-Equal 'no arguments read stdin' 0 $options.Files.Count
}
