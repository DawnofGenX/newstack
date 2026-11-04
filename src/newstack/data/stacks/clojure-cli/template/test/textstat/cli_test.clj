(ns textstat.cli-test
  (:require [clojure.string :as str]
            [clojure.test :refer :all]
            [textstat.cli :as cli]
            [textstat.options :as options]))

;; A fake environment: fixed files, fixed stdin, captured output.
(defn fake-io [files & [stdin]]
  (let [out (atom [])
        err (atom [])]
    {:read-file (fn [path]
                  (if-let [content (get files path)]
                    [true (.getBytes content "UTF-8")]
                    [false (str "cannot open '" path "'")]))
     :read-stdin (fn [] (.getBytes (or stdin "") "UTF-8"))
     :out (fn [line] (swap! out conj line))
     :err (fn [line] (swap! err conj line))
     :out-lines (fn [] @out)
     :err-lines (fn [] @err)}))

(def files
  {"a.txt" "alpha beta\ngamma\n"
   "b.txt" "one\n"})

(deftest a-readable-file-prints-one-row-and-exits-0
  (let [io (fake-io files)]
    (is (= (cli/run ["a.txt"] io) 0))
    (is (= ((:out-lines io)) [" 2  3 17 a.txt"]))
    (is (= ((:err-lines io)) []))))

(deftest columns-are-right-aligned-to-the-widest-figure
  (let [io (fake-io {"big.txt" (apply str (repeat 12 "x "))})]
    (is (= (cli/run ["big.txt"] io) 0))
    (is (= ((:out-lines io)) [" 0 12 24 big.txt"]))))

(deftest more-than-one-file-adds-a-total-row
  (let [io (fake-io files)]
    (is (= (cli/run ["a.txt" "b.txt"] io) 0))
    (is (= ((:out-lines io)) [" 2  3 17 a.txt" " 1  1  4 b.txt" " 3  4 21 total"]))))

(deftest an-unreadable-file-is-reported-others-still-counted-exit-1
  (let [io (fake-io files)]
    (is (= (cli/run ["missing.txt" "a.txt"] io) 1))
    (is (= ((:out-lines io)) [" 2  3 17 a.txt" " 2  3 17 total"]))
    (is (= ((:err-lines io)) ["error: cannot open 'missing.txt'"]))))

(deftest no-file-argument-reads-stdin
  (let [io (fake-io {} "hi there\n")]
    (is (= (cli/run [] io) 0))
    (is (= ((:out-lines io)) ["1 2 9 -"]))))

(deftest a-lone-dash-is-stdin-too
  (let [io (fake-io {} "hi there\n")]
    (is (= (cli/run ["-"] io) 0))
    (is (= ((:out-lines io)) ["1 2 9 -"]))))

(deftest a-single-figure-prints-only-that-column
  (let [io (fake-io files)]
    (is (= (cli/run ["-w" "a.txt"] io) 0))
    (is (= ((:out-lines io)) ["3 a.txt"]))))

(deftest help-exits-0-and-prints-usage-on-stdout
  (let [io (fake-io {})]
    (is (= (cli/run ["--help"] io) 0))
    (is (= ((:err-lines io)) []))
    (is (str/includes? (apply str ((:out-lines io))) "Usage:"))))

(deftest version-exits-0
  (let [io (fake-io {})]
    (is (= (cli/run ["--version"] io) 0))
    (is (= ((:out-lines io)) [options/version]))))

(deftest a-usage-error-exits-2-and-explains-itself-on-stderr
  (let [io (fake-io {})]
    (is (= (cli/run ["--bogus"] io) 2))
    (is (= ((:out-lines io)) []))
    (is (str/includes? (first ((:err-lines io))) "--bogus"))))

(deftest help-wins-over-a-usage-error-that-comes-later
  (let [io (fake-io {})]
    (is (= (cli/run ["--help" "--bogus"] io) 0))))
