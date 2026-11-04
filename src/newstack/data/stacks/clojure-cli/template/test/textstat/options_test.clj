(ns textstat.options-test
  (:require [clojure.string :as str]
            [clojure.test :refer :all]
            [textstat.counts :as counts]
            [textstat.options :as options]))

(deftest no-arguments-means-every-figure-and-stdin
  (let [parsed (options/parse [])]
    (is (= (:figures parsed) counts/all-figures))
    (is (= (:files parsed) []))
    (is (= (:status parsed) :ok))))

(deftest short-flags-combine-in-any-order
  (is (= (:figures (options/parse ["-lw"]))
         {:lines true :words true :bytes false}))
  (is (= (:figures (options/parse ["-wl"]))
         {:lines true :words true :bytes false}))
  (is (= (:figures (options/parse ["-c" "-l"]))
         {:lines true :words false :bytes true})))

(deftest long-flags-are-accepted-too
  (is (= (:figures (options/parse ["--words"]))
         {:lines false :words true :bytes false})))

(deftest flags-before-and-after-files-both-apply
  (let [parsed (options/parse ["-l" "a.txt" "-w" "b.txt"])]
    (is (= (:figures parsed) {:lines true :words true :bytes false}))
    (is (= (:files parsed) ["a.txt" "b.txt"]))))

(deftest double-dash-ends-flag-parsing
  (let [parsed (options/parse ["--" "-w" "file"])]
    (is (= (:figures parsed) counts/all-figures))
    (is (= (:files parsed) ["-w" "file"]))))

(deftest a-lone-dash-is-stdin-not-a-flag
  (is (= (:files (options/parse ["-"])) ["-"])))

(deftest help-and-version-short-circuit
  (is (= (:status (options/parse ["-h"])) :help))
  (is (= (:status (options/parse ["--help"])) :help))
  (is (= (:status (options/parse ["-V"])) :version))
  (is (= (:status (options/parse ["--version"])) :version)))

(deftest an-unknown-short-flag-is-a-usage-error
  (let [parsed (options/parse ["-x"])]
    (is (= (:status parsed) :usage-error))
    (is (str/includes? (:message parsed) "-x"))))

(deftest an-unknown-long-flag-is-a-usage-error
  (let [parsed (options/parse ["--bogus"])]
    (is (= (:status parsed) :usage-error))
    (is (str/includes? (:message parsed) "--bogus"))))

(deftest one-bad-flag-in-a-cluster-is-still-reported
  (let [parsed (options/parse ["-lx"])]
    (is (= (:status parsed) :usage-error))
    (is (str/includes? (:message parsed) "-x"))))
