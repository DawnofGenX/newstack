
# Per-column summary of a CSV: n, mean, min, max, NA count.

csv_summary <- function(path) {
  df <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  cols <- names(df)
  out <- list()
  for (col in cols) {
    x <- df[[col]]
    n <- length(x)
    na_count <- sum(is.na(x))
    if (is.numeric(x)) {
      vals <- x
    } else {
      vals <- suppressWarnings(as.numeric(x))
    }
    if (all(is.na(vals))) {
      mean_val <- NA_real_
      min_val <- NA_real_
      max_val <- NA_real_
    } else {
      mean_val <- mean(vals, na.rm = TRUE)
      min_val <- min(vals, na.rm = TRUE)
      max_val <- max(vals, na.rm = TRUE)
    }
    out[[col]] <- list(name = col, n = n, mean = mean_val, min = min_val, max = max_val, na = na_count)
  }
  out
}

format_csv_summary <- function(summary) {
  lines <- vapply(summary, function(s) {
    paste(s$name, s$n, sprintf("%.6g", s$mean), sprintf("%.6g", s$min), sprintf("%.6g", s$max), s$na, sep = " ")
  }, character(1))
  paste(lines, collapse = "\n")
}
