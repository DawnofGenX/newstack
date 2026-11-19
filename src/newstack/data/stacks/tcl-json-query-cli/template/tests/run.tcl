set here [file dirname [file normalize [info script]]]
source [file join $here .. lib json.tcl]
source [file join $here .. lib query.tcl]

set pass 0
set fail 0
proc failmsg {msg} { global fail; incr fail; puts "FAIL: $msg" }

set json_text "{\"a\":{\"b\":\[10,20\]},\"c\":3}"
set doc [::json::parse $json_text]

if {[::jsonquery::query $doc "a.b.0"] == 10} { incr pass } else { failmsg "nested index" }
if {[::jsonquery::query $doc "a.b.1"] == 20} { incr pass } else { failmsg "nested index2" }
if {[::jsonquery::query $doc "c"] == 3} { incr pass } else { failmsg "scalar" }
set p {a.b[1]}
if {[::jsonquery::query $doc $p] == 20} { incr pass } else { failmsg "bracket index" }

set json_text2 "{\"name\":\"alice\"}"
set doc2 [::json::parse $json_text2]
if {[::jsonquery::query $doc2 "name"] eq "alice"} { incr pass } else { failmsg "string" }

puts "$pass passed, $fail failed"
if {$fail > 0} { exit 1 }
