# Test runner: source the harness, the library, and every *_test.R, then finish.
# Run with: Rscript tests/run.R

# Resolve the project root from this file's location so the runner works from
# any working directory.
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) >= 1) {
  this_file <- sub("^--file=", "", file_arg[1])
} else {
  this_file <- args[2]
}
root <- normalizePath(file.path(dirname(normalizePath(this_file, mustWork = FALSE)), ".."), mustWork = FALSE)

source(file.path(root, "tests", "harness.R"))
source(file.path(root, "R", "counts.R"))
source(file.path(root, "R", "options.R"))

for (f in c("counts_test.R", "options_test.R", "cli_test.R")) {
  source(file.path(root, "tests", f))
}

finish()
