# A fake process boundary so the runner can be exercised without a real one.
namespace eval ::textstat::test {}

set ::textstat::test::stdin ""
set ::textstat::test::files {}

proc ::textstat::test::read-file {path} {
    if {![dict exists $::textstat::test::files $path]} {
        error "no such file: $path"
    }
    return [dict get $::textstat::test::files $path]
}

proc ::textstat::test::read-stdin {} {
    return $::textstat::test::stdin
}

proc ::textstat::test::dir {} {
    set dir [file join [file dirname [file normalize [info script]]] ".." ".test-tmp"]
    file mkdir $dir
    return $dir
}

# @return [list] exit code, stdout, stderr - each trailing newline stripped
proc ::textstat::test::run {argv stdin fileMap} {
    set ::textstat::test::stdin $stdin
    set ::textstat::test::files $fileMap
    set dir [::textstat::test::dir]
    set outPath [file join $dir out.txt]
    set errPath [file join $dir err.txt]
    set outChannel [open $outPath w]
    set errChannel [open $errPath w]
    set io [dict create \
        readFile ::textstat::test::read-file \
        readStdin ::textstat::test::read-stdin \
        out $outChannel \
        err $errChannel]
    set failed [catch {::textstat::runner::run $argv $io} code]
    close $outChannel
    close $errChannel
    set outText [string trimright [::textstat::test::slurp $outPath] "\n"]
    set errText [string trimright [::textstat::test::slurp $errPath] "\n"]
    if {$failed} {
        return [list 99 $outText "runner error: $code"]
    }
    return [list $code $outText $errText]
}

proc ::textstat::test::slurp {path} {
    set channel [open $path r]
    set text [read $channel]
    close $channel
    return $text
}
