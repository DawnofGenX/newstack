(ns textstat.run-tests
  (:require [clojure.test :refer [run-tests successful?]]))

;; Run the whole suite non-interactively and exit non-zero if any test fails,
;; so the gate (and CI) can rely on the process status. The test namespaces are
;; required first so their `deftest` forms register; `run-tests` then returns a
;; summary map, and `successful?` is true only when :fail and :error are zero.
(defn -main []
  (require 'textstat.counts-test 'textstat.options-test 'textstat.cli-test)
  (let [summary (run-tests 'textstat.counts-test 'textstat.options-test 'textstat.cli-test)]
    (if (successful? summary)
      (System/exit 0)
      (System/exit 1))))
