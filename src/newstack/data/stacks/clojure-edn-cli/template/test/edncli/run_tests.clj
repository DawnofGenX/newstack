(ns edncli.run-tests
  (:require [clojure.test :refer [run-tests successful?]]))

(defn -main []
  (require 'edncli.core-test 'edncli.cli-test)
  (let [summary (run-tests 'edncli.core-test 'edncli.cli-test)]
    (if (successful? summary)
      (System/exit 0)
      (System/exit 1))))