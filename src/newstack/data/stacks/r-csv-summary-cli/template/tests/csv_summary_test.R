
describe("csv summary", function() {
  tmp <- tempfile(fileext = ".csv")
  writeLines(c("x,y", "1,2", "3,4", "5,"), tmp)
  s <- csv_summary(tmp)
  expect_equal(s$x$n, 3L, "x n")
  expect_equal(s$x$mean, 3, "x mean")
  expect_equal(s$x$min, 1L, "x min")
  expect_equal(s$x$max, 5L, "x max")
  expect_equal(s$x$na, 0L, "x na")
  expect_equal(s$y$na, 1L, "y na count")
  unlink(tmp)
})
