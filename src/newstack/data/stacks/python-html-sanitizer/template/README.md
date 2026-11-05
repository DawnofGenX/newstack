# {{ title }}

An allowlist HTML sanitizer that rebuilds the markup instead of filtering it.

Nothing from the input is copied through: the document is parsed into events and
the output is *written* from the events the policy allows. That is the difference
between "we removed the tags we know about" and "only these tags can exist".

No dependencies outside the standard library.

## Quick start

```
uv venv
uv pip install -e . pytest ruff

$ echo '<p onclick="steal()">hi</p>' | {{ npm_name }} render
<p>hi</p>
dropped  0 tag(s), 1 attribute(s), 0 url(s) refused, 0 content block(s)

$ echo '<a href="javascript:alert(1)">click</a>' | {{ npm_name }} render --json
{
  "output": "<a>click</a>",
  "stats": {
    "attributes_dropped": 0,
    "characters_dropped": 0,
    "comments_dropped": 0,
    "content_dropped": 0,
    "tags_dropped": 0,
    "urls_refused": 1
  }
}

$ {{ npm_name }} policy
tags     a abbr b blockquote br code del div em h1 h2 h3 h4 h5 h6 hr i ins li ol p pre q s small span strong sub sup table tbody td th thead tr u ul
attrs    a: href title
attrs    blockquote: cite
attrs    q: cite
attrs    td: colspan rowspan
attrs    th: colspan rowspan scope
schemes  http https mailto tel
comments dropped
content  always dropped inside: embed frame frameset iframe math noscript object script style svg template
void     never closed: area base br col embed hr img input link meta param source track wbr

$ {{ npm_name }} check page.html link.html
ok       page.html
ok       link.html

$ PY=.venv/bin/python bash smoke.sh
40 passed, 0 failed
smoke: all checks passed
```

The counters go to stderr; the sanitized document goes to stdout, so the
command composes in a pipe.

## Commands

```
render [--file PATH|-] [--json]   sanitize a file (default: stdin)
check FILE... [--json]            audit each file's output; exit 1 if any fails
policy                            print the allowlist in use
demo                              eight vectors, with what each one proves
selftest                          the same claims, without the prose
```

Exit codes: `0` fine, `1` a file failed the audit, `2` unusable input (missing
file, not UTF-8, no command).

## The demo, verbatim

```
a script block                   as advertised
  in       <p>hello</p><script>alert(1)</script><p>bye</p>
  out      '<p>hello</p><p>bye</p>'
  the payload is gone, not escaped
  ok       nothing dangerous survives, and the output is a fixed point

an image with an event handler   as advertised
  in       <img src=x onerror="alert(1)">
  out      ''
  the tag is dropped, and it has no text to keep
  ok       nothing dangerous survives, and the output is a fixed point

a javascript url                 as advertised
  in       <a href="javascript:alert(1)">click</a>
  out      '<a>click</a>'
  the link survives, the url does not
  ok       nothing dangerous survives, and the output is a fixed point

a url that hides its scheme      as advertised
  in       <a href="jav&#x09;ascript&#58;alert(1)">x</a>
  out      '<a>x</a>'
  a tab inside the scheme changes nothing
  ok       nothing dangerous survives, and the output is a fixed point

attributes nobody allowed        as advertised
  in       <p onclick="steal()" style="color:red">text</p>
  out      '<p>text</p>'
  the element stays, its handlers do not
  ok       nothing dangerous survives, and the output is a fixed point

markup that does not nest        as advertised
  in       <b><i>bold italic</b></i>
  out      '<b><i>bold italic</i></b>'
  the output is closed in the order it was opened
  ok       nothing dangerous survives, and the output is a fixed point

text that looks like markup      as advertised
  in       5 < 6 & 7 > 2
  out      '5 &lt; 6 &amp; 7 &gt; 2'
  characters are escaped, not sanitized away
  ok       nothing dangerous survives, and the output is a fixed point

a comment                        as advertised
  in       <p>visible</p><!-- secret -->
  out      '<p>visible</p>'
  comments are not content
  ok       nothing dangerous survives, and the output is a fixed point

demo: 8 vectors, 0 not as advertised
```

## Eight things this gets right

1. **Dropping the tag is not dropping the hazard.** `<script>` must go with its
   body; the body is what a browser would run. `style`, `iframe`, `object`,
   `svg` and friends are in the same list, and the removed characters are
   counted so the loss is visible.
2. **A scheme is what the browser sees, not what you typed.** Browsers discard
   ASCII whitespace and control characters *inside* a URL scheme, so
   `java&#x09;script:` is `javascript:`. The value is entity-decoded by the
   parser first, then stripped the same way, then compared against
   `http`, `https`, `mailto`, `tel`.
3. **Unknown schemes are refused, not assumed relative.** `foo:bar` has a
   scheme. Relative URLs (`/x`, `#top`, `a/b:c`) have none and are allowed.
4. **Attributes are per tag.** `href` on an `a` is fine; `href` on a `p` is not.
   The default policy allows no `style` anywhere and no `on*` event handler
   anywhere, and an attribute with no value is dropped rather than guessed.
5. **Output is written, never patched.** Attributes are emitted sorted, quoted
   with `"`, and escaped; text is escaped with `&lt;`, `&amp;`, `&gt;`. There is
   no code path that copies input bytes to the output.
6. **Broken nesting is repaired, not preserved.** `<b><i>x</b></i>` becomes
   `<b><i>x</i></b>`; a stray close tag is dropped; every element the output
   opens, it closes.
7. **The result is a fixed point.** `sanitize(sanitize(x)) == sanitize(x)` is
   checked for every vector, because the usual sanitizer bug is an output that a
   second pass changes — which means one browser sees a different document than
   another.
8. **The audit reads the OUTPUT.** `check` scans the emitted tags for script,
   iframe, plugin and style tags, `javascript:`/`vbscript:`/`data:text/html`
   URLs and `on*=`, and also re-runs the sanitizer to prove the fixed point.
   Scanning the input would only prove the input was dangerous.

## What this is not

Not a full HTML parser, not a browser-accurate tree builder, and not a
protection against a *browser bug*: it produces markup that only ever contains
allowed constructs, which is the strongest claim a tool of this size can make.
It does not keep unknown entities as entities — an unknown `&foo;` becomes
`&amp;foo;`, which renders as text instead of guessing.

## Layout

| path | what it holds |
| --- | --- |
| `src/{{ package_name }}/policy.py` | the allowlist, as data, with contradictions refused |
| `src/{{ package_name }}/sanitize.py` | the parser that writes, `scheme_of`, `Stats` |
| `src/{{ package_name }}/audit.py` | the output-side danger scan and the fixed-point check |
| `src/{{ package_name }}/demo.py` | the eight vectors above |
| `src/{{ package_name }}/cli.py` | `render`, `check`, `policy`, `demo`, `selftest` |
