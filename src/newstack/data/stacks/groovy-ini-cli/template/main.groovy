import IniReader

def usage() {
    println "Usage: {{ npm_name }} [OPTION]... [FILE]..."
    println "Read an INI file with typed values."
    println "  --get KEY   print the typed value for KEY (section.key or key)"
    println "  -h, --help  print this help"
}

if (args.length == 0) {
    usage()
    System.exit(2)
}

def getOpt = null
def file = null
def i = 0
while (i < args.length) {
    def a = args[i]
    if (a == "--get") {
        if (i + 1 >= args.length) { usage(); System.exit(2) }
        getOpt = args[i + 1]
        i += 2
        continue
    } else if (a == "-h" || a == "--help") {
        usage()
        System.exit(0)
    } else if (a.startsWith("-")) {
        println "{{ npm_name }}: unknown option: ${a}"
        usage()
        System.exit(2)
    } else {
        if (file != null) { println "{{ npm_name }}: too many files"; System.exit(2) }
        file = a
        i++
    }
}

if (file == null) { usage(); System.exit(2) }

def text
try {
    text = new File(file).getText("UTF-8")
} catch (Exception e) {
    println "{{ npm_name }}: cannot open '${file}'"
    System.exit(1)
}

def data
try {
    data = IniReader.parse(text)
} catch (Exception e) {
    println "{{ npm_name }}: ${e.message}"
    System.exit(1)
}

if (getOpt != null) {
    def value
    try {
        value = IniReader.get(data, getOpt)
    } catch (Exception e) {
        println "{{ npm_name }}: ${e.message}"
        System.exit(1)
    }
    println IniReader.format(value)
    System.exit(0)
}

// dump
data.each { section, entries ->
    entries.each { key, value ->
        println "${section}.${key}=${IniReader.format(value)}"
    }
}
System.exit(0)
