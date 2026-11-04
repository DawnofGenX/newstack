// The only file that touches the real process: the filesystem, standard input
// and the two output streams. Everything else is decided in src/textstat.
import textstat.Runner

def readFile = { String path ->
    File file = new File(path)
    if (!file.isFile() || !file.canRead()) {
        throw new FileNotFoundException("cannot open ${path}")
    }
    return file.bytes
}

def readStdin = { ->
    return System.in.bytes
}

def writeOut = { String text ->
    System.out.print(text)
    System.out.flush()
    return null
}

def writeErr = { String text ->
    System.err.print(text)
    System.err.flush()
    return null
}

def runner = new Runner(
    readFile: readFile,
    readStdin: readStdin,
    out: writeOut,
    err: writeErr,
)

System.exit(runner.run((args as List<String>)))
