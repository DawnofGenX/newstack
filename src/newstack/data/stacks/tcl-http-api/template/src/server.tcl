# The socket half: accept one connection, read one request, call the route
# table, write one response, close. Response documents always carry
# `connection: close`, so there is no keep-alive state to get wrong.

namespace eval textstat::server {}

proc textstat::server::reason {status} {
    switch -- $status {
        200 { return "OK" }
        404 { return "Not Found" }
        405 { return "Method Not Allowed" }
        422 { return "Unprocessable Entity" }
        default { return "Internal Server Error" }
    }
}

proc textstat::server::read_request {chan} {
    set request_line [gets $chan line]
    if {$request_line < 0} {
        return [dict create ok 0 reason "empty request"]
    }

    set headers [dict create]
    while {1} {
        if {[gets $chan header] < 0} {
            return [dict create ok 0 reason "headers ended early"]
        }
        set header [string trimright $header "\r"]
        if {$header eq ""} {
            break
        }
        set colon [string first ":" $header]
        if {$colon < 0} {
            continue
        }
        set name [string tolower [string trim [string range $header 0 [expr {$colon - 1}]]]]
        set value [string trim [string range $header [expr {$colon + 1}] end]]
        dict set headers $name $value
    }

    set line [string trimright $line "\r"]
    if {![regexp {^([A-Z]+) (\S+)} $line -> method target]} {
        return [dict create ok 0 reason "malformed request line"]
    }

    set body ""
    if {[dict exists $headers content-length]} {
        set declared [dict get $headers content-length]
        if {[string is integer -strict $declared] && $declared > 0} {
            set body [read $chan $declared]
            if {[string length $body] < $declared} {
                return [dict create ok 0 reason "body shorter than Content-Length"]
            }
        }
    }

    if {[regexp {^([^?]*)\??(.*)$} $target -> path query]} {
        # regexp already split the target; nothing else to do here.
    } else {
        return [dict create ok 0 reason "malformed target"]
    }

    return [dict create ok 1 method $method path $path query $query body $body]
}

proc textstat::server::respond {chan status body} {
    set head [format "HTTP/1.1 %d %s\r\ncontent-type: application/json\r\ncontent-length: %d\r\nconnection: close\r\n\r\n" \
        $status [reason $status] [string length $body]]
    puts -nonewline $chan $head
    puts -nonewline $chan $body
    flush $chan
}

proc textstat::server::handle {chan addr port} {
    fconfigure $chan -translation binary -buffering none
    if {[catch {
        set request [read_request $chan]
        if {![dict get $request ok]} {
            respond $chan 422 "{\"error\":\"invalid_json\",\"detail\":\"[textstat::contract::json_escape [dict get $request reason]]\"}"
        } else {
            set reply [textstat::contract::route \
                [dict get $request method] [dict get $request path] \
                [dict get $request query] [dict get $request body]]
            respond $chan [dict get $reply status] [dict get $reply body]
        }
    } err]} {
        catch {respond $chan 500 "{\"error\":\"internal_error\"}"}
    }
    catch {close $chan}
}

proc textstat::server::serve {host port} {
    set listener [socket -server textstat::server::handle -myaddr $host $port]
    vwait textstat::server::forever
    return $listener
}
