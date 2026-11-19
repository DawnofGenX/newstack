namespace eval ::b64::test::codec {}

# @return [string] the input's bytes, UTF-8 encoded
proc ::b64::test::codec::bytes {text} {
    return [encoding convertto utf-8 $text]
}

proc ::b64::test::codec::run {} {
    set checks 0

    # RFC 4648 section 10
    set vectors {
        "" ""
        "f" "Zg=="
        "fo" "Zm8="
        "foo" "Zm9v"
        "foob" "Zm9vYg=="
        "fooba" "Zm9vYmE="
        "foobar" "Zm9vYmFy"
    }
    foreach {plain encoded} $vectors {
        ::harness::check "encode '$plain'" [::b64::encode [bytes $plain]] $encoded
        ::harness::check "decode '$encoded'" [::b64::decode $encoded] [bytes $plain]
        incr checks
    }

    # the URL-safe alphabet swaps +/ for -_ and usually drops padding
    set payload [binary format H* "fbff"]
    ::harness::check "standard alphabet" [::b64::encode $payload] "+/8="
    ::harness::check "url alphabet" [::b64::encode $payload {url 1 padding 0}] "-_8"
    ::harness::check "url decodes back" [::b64::to-hex [::b64::decode "-_8"]] "fbff"

    # padding is optional on input, whitespace is ignored
    ::harness::check "unpadded input" [::b64::decode "Zm9vYg"] "foob"
    ::harness::check "whitespace input" [::b64::decode "Zm9v\nYmFy "] "foobar"

    # hex helpers round-trip and reject nonsense
    ::harness::check "to-hex" [::b64::to-hex [binary format H* "00ff10"]] "00ff10"
    ::harness::check "from-hex" [::b64::to-hex [::b64::from-hex "00FF10"]] "00ff10"
    set hexFailed 0
    foreach {bad expectedMessage} {
        "abc" {hex input needs an even number of digits, got 3}
        "zz" {hex input contains a non-hex character}
    } {
        if {[catch {::b64::from-hex $bad} message] && $message eq $expectedMessage} {
            incr hexFailed 0
        } else {
            incr hexFailed
        }
    }
    ::harness::check "hex errors" $hexFailed 0

    # malformed base64 is refused, and the messages say why
    set refusals {
        "Zm9vY" truncated
        "Zm9v!" invalid
        "Zm9vYg=A" padding
    }
    foreach {bad fragment} $refusals {
        ::harness::check "refuses '$bad'" [expr {[catch {::b64::decode $bad} message] && [string first $fragment $message] >= 0 ? "yes" : "no: $message"}] "yes"
    }

    return $checks
}
