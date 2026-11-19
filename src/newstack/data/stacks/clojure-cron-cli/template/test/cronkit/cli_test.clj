(ns cronkit.cli-test
  (:require [clojure.string :as str]
            [clojure.test :refer :all]
            [cronkit.cli :as cli]))

(defn fake-io []
  (let [out (atom [])
        err (atom [])]
    {:out (fn [line] (swap! out conj line))
     :err (fn [line] (swap! err conj line))
     :out-lines (fn [] @out)
     :err-lines (fn [] @err)}))

(deftest help-exits-zero
  (let [io (fake-io)]
    (is (= 0 (cli/run-command ["--help"] io)))
    (is (str/starts-with? (first ((:out-lines io))) "Usage: "))
    (is (= [] ((:err-lines io))))))

(deftest version-is-printed
  (let [io (fake-io)]
    (is (= 0 (cli/run-command ["-V"] io)))
    (is (= ["0.1.0"] ((:out-lines io))))))

(deftest three-runs-are-printed
  (let [io (fake-io)
        status (cli/run-command ["-n" "3" "--from" "2024-01-01T00:00:00Z" "*/15" "*" "*" "*" "*" ] io)]
    (is (= 0 status))
    (is (= ["2024-01-01T00:15:00Z" "2024-01-01T00:30:00Z" "2024-01-01T00:45:00Z"]
           ((:out-lines io))))))

(deftest a-quoted-expression-works-too
  (let [io (fake-io)]
    (is (= 0 (cli/run-command ["-n" "1" "--from" "2024-01-01T00:00:00Z" "30 4 * * *"] io)))
    (is (= ["2024-01-01T04:30:00Z"] ((:out-lines io))))))

(deftest explain-prints-each-field-first
  (let [io (fake-io)]
    (is (= 0 (cli/run-command ["--explain" "-n" "1" "--from" "2024-01-01T00:00:00Z" "0 9 * * 1-5"] io)))
    (let [lines ((:out-lines io))]
      (is (str/starts-with? (first lines) "expression  : 0 9 * * 1-5"))
      (is (some #(str/starts-with? % "day of week ") lines))
      (is (= "2024-01-01T09:00:00Z" (last lines))))))

(deftest a-date-only-from-is-midnight-utc
  (let [io (fake-io)]
    (is (= 0 (cli/run-command ["-n" "1" "--from" "2024-03-01" "0 0 1 * *"] io)))
    (is (= ["2024-04-01T00:00:00Z"] ((:out-lines io))))))

(deftest a-bad-expression-exits-two
  (let [io (fake-io)]
    (is (= 2 (cli/run-command ["61" "*" "*" "*" "*"] io)))
    (is (str/includes? (first ((:err-lines io))) "outside 0-59"))))

(deftest a-bad-instant-exits-two
  (let [io (fake-io)]
    (is (= 2 (cli/run-command ["--from" "yesterday" "*" "*" "*" "*" "*"] io)))
    (is (str/includes? (first ((:err-lines io))) "cannot read 'yesterday'"))))

(deftest a-missing-expression-exits-two
  (let [io (fake-io)]
    (is (= 2 (cli/run-command [] io)))
    (is (str/includes? (first ((:err-lines io))) "missing the cron expression"))))

(deftest an-impossible-schedule-exits-one
  (let [io (fake-io)]
    (is (= 1 (cli/run-command ["0" "0" "31" "2" "*"] io)))
    (is (str/includes? (first ((:err-lines io))) "never fires"))))
