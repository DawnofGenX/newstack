import yaml.Yaml

def readFile = { String path ->
    File file = new File(path)
    if (!file.isFile() || !file.canRead()) {
        throw new FileNotFoundException("cannot open ${path}")
    }
    return file.text
}

def readStdin = { -> System.in.text }

def argsList = args as List<String>

if (argsList.contains('--help') || argsList.contains('-h')) {
    println "Usage: {{ npm_name }} [FILE]"
    println "Print flattened keys of a YAML document."
    System.exit(0)
}

String input
if (argsList.isEmpty() || argsList == ['-']) {
    input = readStdin()
} else if (argsList.size() == 1) {
    try {
        input = readFile(argsList[0])
    } catch (Exception e) {
        System.err.println("error: ${e.message}")
        System.exit(1)
    }
} else {
    System.err.println("usage: {{ npm_name }} [FILE]")
    System.exit(2)
}

try {
    String out = Yaml.render(input)
    print out
    if (!out.endsWith('\n')) println ''
} catch (Exception e) {
    System.err.println("error: ${e.message}")
    System.exit(1)
}
System.exit(0)