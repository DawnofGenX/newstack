package textstat

/** The argv parser: a plain list walk, no external dependency. */
class Options {
    static final String VERSION = '0.1.0'
    static final List<String> ALL_FIGURES = ['lines', 'words', 'bytes'].asImmutable()

    String status = 'ok'
    String message = ''
    List<String> figures = []
    List<String> files = []

    static String usage(String program) {
        String text = "Usage: ${program} [OPTION]... [FILE]...\n"
        text += '\n'
        text += 'Print newline, word, and byte counts for each FILE.\n'
        text += '\n'
        text += '  -l, --lines    print the newline counts\n'
        text += '  -w, --words    print the word counts\n'
        text += '  -c, --bytes    print the byte counts\n'
        text += '  -h, --help     show this help and exit\n'
        text += '  -V, --version  show the version and exit\n'
        text += '\n'
        text += 'With no FILE, or when FILE is -, read standard input.\n'
        return text
    }

    static Options parse(List<String> args) {
        Options options = new Options()
        boolean literal = false
        boolean sawFigure = false

        for (String arg : args) {
            if (!literal && arg == '--') {
                literal = true
                continue
            }
            if (!literal && arg.startsWith('--')) {
                switch (arg) {
                    case '--lines':
                        options.addFigure('lines')
                        sawFigure = true
                        break
                    case '--words':
                        options.addFigure('words')
                        sawFigure = true
                        break
                    case '--bytes':
                        options.addFigure('bytes')
                        sawFigure = true
                        break
                    case '--help':
                        options.status = 'help'
                        return options
                    case '--version':
                        options.status = 'version'
                        return options
                    default:
                        options.status = 'usage-error'
                        options.message = "unknown option: ${arg}"
                        return options
                }
                continue
            }
            if (!literal && arg.length() > 1 && arg.startsWith('-')) {
                for (int index = 1; index < arg.length(); index++) {
                    String letter = arg.substring(index, index + 1)
                    switch (letter) {
                        case 'l':
                            options.addFigure('lines')
                            sawFigure = true
                            break
                        case 'w':
                            options.addFigure('words')
                            sawFigure = true
                            break
                        case 'c':
                            options.addFigure('bytes')
                            sawFigure = true
                            break
                        case 'h':
                            options.status = 'help'
                            return options
                        case 'V':
                            options.status = 'version'
                            return options
                        default:
                            options.status = 'usage-error'
                            options.message = "unknown option: -${letter}"
                            return options
                    }
                }
                continue
            }
            options.files << arg
        }

        if (!sawFigure) {
            options.figures = new ArrayList<String>(ALL_FIGURES)
        }
        // wc always prints the figures in this order, whatever the flag order.
        options.figures = ALL_FIGURES.findAll { String name -> options.figures.contains(name) }
        return options
    }

    private void addFigure(String name) {
        if (!figures.contains(name)) {
            figures << name
        }
    }
}
