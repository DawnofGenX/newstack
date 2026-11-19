(ns cronkit.schedule-test
  (:require [clojure.test :refer :all]
            [cronkit.schedule :as schedule])
  (:import [java.time Instant]))

(defn at [text] (Instant/parse text))

(deftest a-star-field-covers-the-whole-range
  (let [parsed (schedule/parse "* * * * *")]
    (is (= 60 (count (:minutes parsed))))
    (is (= 24 (count (:hours parsed))))
    (is (= 31 (count (:days-of-month parsed))))
    (is (= 12 (count (:months parsed))))
    (is (= 7 (count (:days-of-week parsed))))))

(deftest steps-lists-and-ranges-expand
  (is (= #{0 15 30 45} (:minutes (schedule/parse "*/15 * * * *"))))
  (is (= #{1 15 30} (:minutes (schedule/parse "1,15,30 * * * *"))))
  (is (= #{1 2 3 4 5} (:days-of-week (schedule/parse "0 9 * * 1-5"))))
  (is (= #{0 2 4 6} (:hours (schedule/parse "0 0-6/2 * * *"))))
  (is (= #{59} (:minutes (schedule/parse "59 * * * *")))))

(deftest names-are-accepted-in-the-month-and-weekday-fields
  (let [parsed (schedule/parse "0 0 * jan-mar mon")]
    (is (= #{1 2 3} (:months parsed)))
    (is (= #{1} (:days-of-week parsed))))
  (is (= #{0} (:days-of-week (schedule/parse "0 0 * * sun")))))

(deftest seven-is-sunday
  (is (= #{0} (:days-of-week (schedule/parse "0 0 * * 7")))))

(deftest bad-expressions-are-rejected
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "* * * *")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "60 * * * *")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "*/0 * * * *")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "5-1 * * * *")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "0 0 * * 8")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "0 0 * * mon-fri,,")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "0 0 * * xyz")))
  (is (thrown? clojure.lang.ExceptionInfo (schedule/parse "0 0 * *"))))

(deftest the-error-says-what-is-wrong
  (try
    (schedule/parse "60 * * * *")
    (is false "should have thrown")
    (catch clojure.lang.ExceptionInfo error
      (is (.contains (.getMessage error) "outside 0-59")))))

(deftest next-time-is-strictly-after-the-instant
  (let [parsed (schedule/parse "*/15 * * * *")
        runs (schedule/next-times parsed (at "2024-01-01T00:07:00Z") 4)]
    (is (= (map schedule/format-instant runs)
           ["2024-01-01T00:15:00Z" "2024-01-01T00:30:00Z"
            "2024-01-01T00:45:00Z" "2024-01-01T01:00:00Z"]))))

(deftest a-minute-that-matches-is-skipped
  (let [parsed (schedule/parse "0 * * * *")]
    (is (= (schedule/format-instant (schedule/next-time parsed (at "2024-01-01T05:00:00Z")))
           "2024-01-01T06:00:00Z"))))

(deftest weekdays-skip-the-weekend
  (let [parsed (schedule/parse "0 9 * * 1-5")
        runs (schedule/next-times parsed (at "2024-01-05T10:00:00Z") 2)]
    (is (= (map schedule/format-instant runs)
           ["2024-01-08T09:00:00Z" "2024-01-09T09:00:00Z"]))))

(deftest a-leap-day-is-found-years-ahead
  (let [parsed (schedule/parse "0 0 29 2 *")]
    (is (= (schedule/format-instant (schedule/next-time parsed (at "2024-03-01T00:00:00Z")))
           "2028-02-29T00:00:00Z"))))

(deftest an-impossible-date-never-fires
  (let [parsed (schedule/parse "0 0 31 2 *")]
    (is (= [] (schedule/next-times parsed (at "2024-03-01T00:00:00Z") 3)))))

(deftest day-of-month-and-weekday-are-ored
  ;; The 1st to the 7th of January 2024: Friday the 5th and Saturday the 6th are
  ;; Fridays, so the first hit is the 5th; the 13th is the next weekday-only hit.
  (let [parsed (schedule/parse "0 0 13 * 5")
        runs (schedule/next-times parsed (at "2024-01-01T00:00:00Z") 3)]
    (is (= (map schedule/format-instant runs)
           ["2024-01-05T00:00:00Z" "2024-01-12T00:00:00Z" "2024-01-13T00:00:00Z"]))))

(deftest restricted-weekday-alone-needs-the-day-of-month-too
  (let [parsed (schedule/parse "0 0 * * 5")]
    (is (= #{1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31}
           (:days-of-month parsed)))))

(deftest matches-agrees-with-next-time
  (let [parsed (schedule/parse "30 4 * * *")]
    (is (schedule/matches? parsed (at "2024-06-01T04:30:00Z")))
    (is (not (schedule/matches? parsed (at "2024-06-01T04:31:00Z"))))))
