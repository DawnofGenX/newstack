import yaml.Yaml

int failed = 0
def check = { String name, boolean ok ->
    if (ok) println "ok: ${name}"
    else { println "FAIL: ${name}"; failed++ }
}

// pinned known value
def parsed = Yaml.parse("a:\n  b: 1\n  c: hello\n")
check 'nested map', parsed == [a: [b: 1L, c: 'hello']]

def flat = Yaml.flatten(parsed)
check 'flattened count', flat.size() == 2
check 'flattened b', flat.contains('a.b: 1')
check 'flattened c', flat.contains('a.c: hello')

// top-level scalar-ish map
def p2 = Yaml.parse("x: 42\ny: true\nz: null\n")
check 'int', p2.x == 42L
check 'bool', p2.y == true
check 'null', p2.z == null

// error case: empty input yields empty map
def p3 = Yaml.parse("")
check 'empty', p3 == [:]

if (failed > 0) { System.exit(1) } else { System.exit(0) }