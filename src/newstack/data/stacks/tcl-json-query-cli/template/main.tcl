set here [file dirname [file normalize [info script]]]
foreach name {json query} {
    source [file join $here lib "$name.tcl"]
}

if {$argc == 0} {
    puts "usage: [file tail [info script]] <json.path> [FILE]"
    exit 2
}
set path [lindex $argv 0]
set file "-"
if {$argc >= 2} { set file [lindex $argv 1] }

if {$file eq "-"} {
    fconfigure stdin -translation binary
    set data [read stdin]
} else {
    set ch [open $file rb]
    set data [read $ch]
    close $ch
}

set doc [::json::parse $data]
set result [::jsonquery::query $doc $path]
puts $result