(ns cronkit.options-test
  (:require [clojure.test :refer :all]
            [cronkit.options :as options]))

(deftest plain-fields-become-operands
  (let [parsed (options/parse ["*/15" "*" "*" "*" "*"])]
    (is (= :ok (:status parsed)))
    (is (= ["*/15" "*" "*" "*" "*"] (:operands parsed)))
    (is (= 5 (:count parsed)))
    (is (false? (:explain parsed)))))

(deftest count-and-from-are-read
  (let [parsed (options/parse ["-n" "3" "--from" "2024-01-01T00:00:00Z" "*" "*" "*" "*" "*"])]
    (is (= 3 (:count parsed)))
    (is (= "2024-01-01T00:00:00Z" (:from parsed)))
    (is (= ["*" "*" "*" "*" "*"] (:operands parsed)))))

(deftest help-and-version-short-circuit
  (is (= :help (:status (options/parse ["--help"]))))
  (is (= :version (:status (options/parse ["-V"]))))
  (is (= :help (:status (options/parse ["*" "*" "*" "*" "*" "--help"])))))

(deftest a-bad-count-is-a-usage-error
  (is (= :usage-error (:status (options/parse ["-n" "zero"]))))
  (is (= :usage-error (:status (options/parse ["-n" "0"]))))
  (is (= :usage-error (:status (options/parse ["-n"])))))

(deftest unknown-options-are-usage-errors
  (is (= :usage-error (:status (options/parse ["--bogus"]))))
  (is (true? (:explain (options/parse ["--explain" "*" "*" "*" "*" "*"])))))
