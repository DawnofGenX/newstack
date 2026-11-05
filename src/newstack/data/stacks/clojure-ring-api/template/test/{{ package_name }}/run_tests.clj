(ns {{ package_name }}.run-tests
  (:require [clojure.test :refer [run-tests successful?]]))

;; Run every namespace non-interactively and exit non-zero if any assertion
;; fails, so the gate and CI can trust the process status.

(def test-namespaces
  '[{{ package_name }}.counts-test
    {{ package_name }}.handler-test])

(defn -main [& _]
  (apply require test-namespaces)
  (let [summary (apply run-tests test-namespaces)]
    (System/exit (if (successful? summary) 0 1))))
