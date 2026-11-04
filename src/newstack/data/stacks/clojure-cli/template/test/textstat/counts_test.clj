(ns textstat.counts-test
  (:require [clojure.test :refer :all]
            [textstat.counts :as counts]))

(defn counts-of [text]
  (counts/of-bytes (.getBytes text "UTF-8")))

(deftest plain-text-with-a-trailing-newline
  (is (= (counts-of "alpha beta\ngamma delta\n")
         {:lines 2 :words 4 :bytes 23})))

(deftest a-last-line-without-a-trailing-newline-is-not-a-line
  (is (= (counts-of "alpha beta\ngamma")
         {:lines 1 :words 3 :bytes 16})))

(deftest bytes-are-bytes-not-characters
  (is (= (counts-of "héllo wörld\n")
         {:lines 1 :words 2 :bytes 14})))

(deftest empty-input
  (is (= (counts-of "")
         {:lines 0 :words 0 :bytes 0})))

(deftest runs-of-whitespace-separate-words
  (is (= (counts-of "  one\t\ttwo  \n\n three \n")
         {:lines 3 :words 3 :bytes 22})))

(deftest form-feeds-and-vertical-tabs-are-whitespace
  (is (= (counts-of "a\u000bb\u000cc\n")
         {:lines 1 :words 3 :bytes 6})))

(deftest add-sums-every-figure
  (is (= (counts/add {:lines 1 :words 2 :bytes 3}
                     {:lines 4 :words 5 :bytes 6})
         {:lines 5 :words 7 :bytes 9})))
