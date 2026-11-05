(ns {{ package_name }}.counts-test
  (:require [clojure.test :refer [deftest is testing]]
            [{{ package_name }}.counts :refer [count-text counted-json]]))

(deftest counts-match-wc
  (testing "a single line"
    (is (= {:lines 1 :words 2 :bytes 12} (count-text "hello world\n"))))
  (testing "empty text"
    (is (= {:lines 0 :words 0 :bytes 0} (count-text ""))))
  (testing "blank lines count"
    (is (= {:lines 3 :words 1 :bytes 4} (count-text "\n\nx\n"))))
  (testing "whitespace without newlines has no lines and no words"
    (is (= {:lines 0 :words 0 :bytes 4} (count-text "  \t "))))
  (testing "a line without a trailing newline is not a line"
    (is (= {:lines 0 :words 1 :bytes 3} (count-text "abc"))))
  (testing "bytes are UTF-8, not characters"
    (is (= {:lines 1 :words 2 :bytes 14} (count-text "héllo wörld\n"))))
  (testing "an emoji is four bytes"
    (is (= {:lines 1 :words 1 :bytes 5} (count-text "🙂\n")))))

(deftest refuses-non-strings
  (is (thrown? IllegalArgumentException (count-text 42))))

(deftest counted-json-keeps-the-text
  (is (= {:text "a b\n" :lines 1 :words 2 :bytes 4} (counted-json "a b\n"))))
