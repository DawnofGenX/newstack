args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) >= 1) {
  this_file <- sub("^--file=", "", file_arg[1])
} else {
  this_file <- args[2]
}
root <- normalizePath(file.path(dirname(normalizePath(this_file, mustWork = FALSE)), ".."), mustWork = FALSE)
source(file.path(root, "tests", "harness.R"))
source(file.path(root, "R", "csv_summary.R"))
for (f in c("csv_summary_test.R")) {
  source(file.path(root, "tests", f))
}
finish()
