(ns cronkit.run-tests
  (:require [clojure.test :refer [run-tests successful?]]))

;; Run the whole suite non-interactively and exit non-zero if any test fails,
;; so the gate and CI can rely on the process status.
(defn -main []
  (require 'cronkit.schedule-test 'cronkit.options-test 'cronkit.cli-test)
  (let [summary (run-tests 'cronkit.schedule-test 'cronkit.options-test 'cronkit.cli-test)]
    (if (successful? summary)
      (System/exit 0)
      (System/exit 1))))
