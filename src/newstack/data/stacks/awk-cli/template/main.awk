# The only file that runs at all: set the record separator, take the program
# name from the wrapper, and turn the runner's exit code into the process exit
# status.
BEGIN {
    RS = "\0"
    PROGRAM_NAME = (program == "" ? "awk" : program)
    exit cli_run()
}
