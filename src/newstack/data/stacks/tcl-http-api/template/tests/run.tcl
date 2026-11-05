#!/usr/bin/env tclsh
# A framework-free suite: 24 checks, no tcltest, no socket.
set here [file dirname [file normalize [info script]]]
set root [file join $here .. src]
foreach module {json counts contract server} {
    source [file join $root $module.tcl]
}

set ::passed 0
set ::failed 0

proc check {name got want} {
    if {$got eq $want} {
        incr ::passed
        return
    }
    incr ::failed
    puts stderr "FAIL $name\n  got:  $got\n  want: $want"
}

proc counts_of {text} {
    set counts [textstat::counts::count_text $text]
    return [format "%d/%d/%d" [dict get $counts lines] [dict get $counts words] [dict get $counts bytes]]
}

proc route {method path query body} {
    set reply [textstat::contract::route $method $path $query $body]
    return [format "%d %s" [dict get $reply status] [dict get $reply body]]
}

# counting ------------------------------------------------------------------
check "hello world" [counts_of "hello world\n"] "1/2/12"
check "empty" [counts_of ""] "0/0/0"
check "blank lines" [counts_of "\n\nx\n"] "3/1/4"
check "spaces only" [counts_of "  \t "] "0/0/4"
check "no newline" [counts_of "abc"] "0/1/3"
check "utf8 bytes" [counts_of "h\xc3\xa9llo w\xc3\xb6rld\n"] "1/2/14"
check "emoji" [counts_of "\xf0\x9f\x99\x82\n"] "1/1/5"
check "tab separated" [counts_of "a\tb"] "0/2/3"
check "carriage return is a space" [counts_of "a\r\nb"] "1/2/4"

# the route table -----------------------------------------------------------
check "health" [route GET /health "" ""] {200 {"status":"ok"}}
check "greeting" [route GET /stats "text=hello%20world%0A" ""] \
    {200 {"text":"hello world\n","lines":1,"words":2,"bytes":12}}
check "blank lines" [route GET /stats "text=a%20b%0Ac%0A" ""] \
    {200 {"text":"a b\nc\n","lines":2,"words":3,"bytes":6}}
check "plus is a space" [route GET /stats "text=a+b" ""] \
    {200 {"text":"a b","lines":0,"words":2,"bytes":3}}
check "empty text is present" [route GET /stats "text=" ""] \
    {200 {"text":"","lines":0,"words":0,"bytes":0}}
check "missing text" [route GET /stats "" ""] {422 {"error":"missing_text"}}
check "posted text" [route POST /stats "" {{"text":"a b\nc\n"}}] \
    {200 {"text":"a b\nc\n","lines":2,"words":3,"bytes":6}}
check "posted number is not text" [route POST /stats "" {{"text":42}}] \
    {422 {"error":"missing_text"}}
check "posted quoted number is text" [route POST /stats "" {{"text":"42"}}] \
    {200 {"text":"42","lines":0,"words":1,"bytes":2}}
check "broken json" [route POST /stats "" "nope"] {422 {"error":"invalid_json"}}
check "trailing data" [route POST /stats "" {{"text":"a"} junk}] {422 {"error":"invalid_json"}}
check "unknown route" [route GET /nope "" ""] \
    {404 {"error":"not_found","detail":"no route for GET /nope"}}
check "wrong method on health" [route DELETE /health "" ""] {405 {"error":"method_not_allowed"}}
check "wrong method on stats" [route PUT /stats "" ""] {405 {"error":"method_not_allowed"}}
check "quotes are escaped" [route POST /stats "" {{"text":"a\"b"}}] \
    {200 {"text":"a\"b","lines":0,"words":1,"bytes":3}}

puts [format "%d checks passed, %d failed" $::passed $::failed]
exit [expr {$::failed == 0 ? 0 : 1}]
