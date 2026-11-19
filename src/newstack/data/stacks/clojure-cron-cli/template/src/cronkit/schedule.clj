(ns cronkit.schedule
  "Parsing and evaluation of five field cron expressions.

  Every field is turned into a set of integers once, at parse time, so
  matching and searching never re-parse the text. Day of month and day of week
  follow the traditional rule: when both are restricted, a day matches if
  either field matches."
  (:require [clojure.string :as str])
  (:import [java.time Instant ZoneOffset ZonedDateTime]
           [java.time.format DateTimeFormatter]))

(def month-names
  {"jan" 1 "feb" 2 "mar" 3 "apr" 4 "may" 5 "jun" 6
   "jul" 7 "aug" 8 "sep" 9 "oct" 10 "nov" 11 "dec" 12})

(def day-names
  {"sun" 0 "mon" 1 "tue" 2 "wed" 3 "thu" 4 "fri" 5 "sat" 6})

(defn- fail [spec message]
  (throw (ex-info (str message " in '" spec "'") {:type :cron/parse :spec spec})))

(defn- value-of [text names low high spec]
  (let [lowered (str/lower-case text)
        resolved (if-let [named (get names lowered)]
                   named
                   (if (re-matches #"\d+" text)
                     (parse-long text)
                     (fail spec (str "unknown value '" text "'"))))]
    (when (or (< resolved low) (> resolved high))
      (fail spec (str "value " resolved " is outside " low "-" high)))
    resolved))

;; One comma separated item: `*`, `*/n`, `a`, `a-b`, `a-b/n`.
(defn- expand-item [item names low high spec]
  (let [[body step-text] (str/split item #"/" 2)
        step (if step-text
               (let [parsed (if (re-matches #"\d+" step-text)
                              (parse-long step-text)
                              (fail spec (str "invalid step '" step-text "'")))]
                 (when (zero? parsed) (fail spec "step must be positive"))
                 parsed)
               1)]
    (when (and step-text (= body "*"))
      (when (> step (- high low)) (fail spec "step is larger than the field")))
    (cond
      (= body "*") (set (range low (inc high) step))
      (str/includes? body "-")
      (let [[from-text to-text] (str/split body #"-" 2)
            from (value-of from-text names low high spec)
            to (value-of to-text names low high spec)]
        (when (> from to) (fail spec (str "range " body " runs backwards")))
        (set (range from (inc to) step)))
      :else
      (let [value (value-of body names low high spec)]
        (if step-text
          (set (range value (inc high) step))
          #{value})))))

(defn- expand-field [text names low high spec]
  (when (str/blank? text) (fail spec "missing field"))
  (reduce (fn [acc item]
            (when (str/blank? item) (fail spec "empty list item"))
            (into acc (expand-item item names low high spec)))
          #{}
          (str/split text #"," -1)))

(defn parse
  "Parses a five field cron expression into a schedule map.
  Throws ex-info with :type :cron/parse when the text is not valid."
  [spec]
  (when-not (string? spec) (fail (str spec) "the expression must be a string"))
  (let [fields (str/split (str/trim spec) #"\s+")]
    (when (not= 5 (count fields))
      (fail spec (str "expected 5 fields, got " (count fields))))
    (let [[minute hour dom month dow] fields
          schedule {:minutes (expand-field minute {} 0 59 spec)
                    :hours (expand-field hour {} 0 23 spec)
                    :days-of-month (expand-field dom {} 1 31 spec)
                    :months (expand-field month month-names 1 12 spec)
                    :days-of-week (set (map #(if (= 7 %) 0 %)
                                            (expand-field dow day-names 0 7 spec)))
                    :dom-restricted? (not= "*" dom)
                    :dow-restricted? (not= "*" dow)
                    :spec (str/trim spec)}]
      (when (empty? (:days-of-week schedule))
        (fail spec "day of week is empty"))
      schedule)))

(defn- day-fires?
  "Day of month and day of week combine with OR when both are restricted, which
  is what makes '0 0 13 * 5' fire on every Friday *and* every 13th."
  [schedule zdt]
  (let [dom-fires? (contains? (:days-of-month schedule) (.getDayOfMonth zdt))
        dow-fires? (contains? (:days-of-week schedule) (.getValue (.getDayOfWeek zdt)))]
    (if (and (:dom-restricted? schedule) (:dow-restricted? schedule))
      (or dom-fires? dow-fires?)
      (and dom-fires? dow-fires?))))

(defn matches?
  "True when the instant falls on a minute the schedule fires at."
  [schedule instant]
  (let [zdt (.atZone ^java.time.Instant instant java.time.ZoneOffset/UTC)]
    (and (contains? (:minutes schedule) (.getMinute zdt))
         (contains? (:hours schedule) (.getHour zdt))
         (contains? (:months schedule) (.getMonthValue zdt))
         (day-fires? schedule zdt))))

(def ^:private iso-formatter
  ;; Instant/toString drops the seconds when they are zero; cron output must not.
  (DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ss'Z'"))

(defn- as-zoned [instant]
  (if (instance? ZonedDateTime instant)
    ^ZonedDateTime instant
    (.atZone ^Instant instant ZoneOffset/UTC)))

(defn format-instant [instant]
  (.format iso-formatter (as-zoned instant)))

(defn- truncate
  "Drops seconds and nanoseconds: cron granularity is one minute."
  [instant]
  (.withSecond (.withNano (.atZone ^java.time.Instant instant java.time.ZoneOffset/UTC) (int 0)) (int 0)))

;; Each branch skips a whole unit it knows cannot fire, so a yearly schedule is
;; found in dozens of steps rather than millions of minutes.
(defn next-time
  "The first firing strictly after `instant`, or nil when the schedule cannot
  fire again (31 February, for instance)."
  [schedule instant]
  (let [deadline (+ (.getYear (truncate instant)) 8)]
    (loop [zdt (.plusMinutes (truncate instant) 1)]
      ;; Any schedule that can fire at all fires within eight years (the leap
      ;; year rule), so passing that year means the date is impossible. This has
      ;; to be an `if`: a bare `when` would fall through into the cond below.
      (if (> (.getYear zdt) deadline)
        nil
        (cond
        (not (contains? (:months schedule) (.getMonthValue zdt)))
        (recur (.withMinute (.withHour (.withDayOfMonth (.plusMonths zdt 1) (int 1)) (int 0)) (int 0)))

        (not (day-fires? schedule zdt))
        (recur (.withMinute (.withHour (.plusDays zdt 1) (int 0)) (int 0)))

        (not (contains? (:hours schedule) (.getHour zdt)))
        (recur (.withMinute (.plusHours zdt 1) (int 0)))

          (not (contains? (:minutes schedule) (.getMinute zdt)))
          (recur (.plusMinutes zdt 1))

          :else zdt)))))

(defn next-times
  "Up to `limit` firings strictly after `instant`, as UTC instants."
  [schedule instant limit]
  (loop [at instant
         taken []]
    (if (= (clojure.core/count taken) limit)
      taken
      (if-let [zdt (next-time schedule at)]
        (recur (.toInstant ^java.time.ZonedDateTime zdt) (conj taken (.toInstant ^java.time.ZonedDateTime zdt)))
        taken))))

(defn describe-field [values]
  (clojure.string/join "," (sort values)))
