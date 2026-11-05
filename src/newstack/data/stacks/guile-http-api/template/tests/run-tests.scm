;;; Runs every suite and reports one tally. No framework, no network.
(use-modules (harness))
(use-modules ((counts-tests) #:prefix counts:))
(use-modules ((contract-tests) #:prefix contract:))

(reset!)
(counts:run-suite)
(contract:run-suite)
(exit (report))
