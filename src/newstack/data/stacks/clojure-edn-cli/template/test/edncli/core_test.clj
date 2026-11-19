(ns edncli.core-test
  (:require [clojure.test :refer [deftest is testing]]
            [edncli.core :as core]))

(deftest read-edn-ok
  (is (= [true 42] (core/read-edn "42")))
  (is (= [true {:a 1}] (core/read-edn "{:a 1}"))))

(deftest read-edn-fail
  (is (false? (first (core/read-edn "{:a")))))

(deftest parse-path-test
  (is (= [:a :b] (core/parse-path "a/b")))
  (is (= [:a :b] (core/parse-path ":a/:b")))
  (is (= [:a] (core/parse-path "a"))))

(deftest get-at-test
  (is (= 2 (core/get-at {:a {:b 2}} "a/b")))
  (is (= 2 (core/get-at {:a {:b 2}} ":a/:b")))
  (is (nil? (core/get-at {:a 1} "x"))))

(deftest pretty-test
  (is (string? (core/pretty {:a 1}))))

(deftest top-keys-test
  (is (= (set (core/top-keys {:a 1 :b 2})) #{:a :b})))