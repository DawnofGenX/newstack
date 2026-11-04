;;; Runs every suite and reports one tally. No framework, no network, no disk.
(use-modules (harness))
(use-modules ((counts-tests) #:prefix counts:))
(use-modules ((options-tests) #:prefix options:))
(use-modules ((runner-tests) #:prefix runner:))

(reset!)
(counts:run-suite)
(options:run-suite)
(runner:run-suite)
(exit (report))
