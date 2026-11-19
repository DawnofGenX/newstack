(ns cronkit.cli
  (:require [clojure.string :as str]
            [cronkit.options :as options]
            [cronkit.schedule :as schedule])
  (:import [java.time Instant LocalDate ZoneOffset]))

(def program "{{ npm_name }}")

(defn- explain-lines [parsed]
  [["expression" (:spec parsed)]
   ["minute" (schedule/describe-field (:minutes parsed))]
   ["hour" (schedule/describe-field (:hours parsed))]
   ["day of month" (schedule/describe-field (:days-of-month parsed))]
   ["month" (schedule/describe-field (:months parsed))]
   ["day of week" (schedule/describe-field (:days-of-week parsed))]])

(defn- run [parsed io]
  (let [text (str/join " " (:operands parsed))
        from-text (or (:from parsed) (str (Instant/now)))
        from (try
               (Instant/parse from-text)
               (catch Exception _
                 (try
                   (.toInstant (.atStartOfDay (LocalDate/parse from-text) ZoneOffset/UTC))
                   (catch Exception _ nil))))]
    (cond
      (str/blank? text)
      (do ((:err io) (str program ": missing the cron expression"))
          ((:err io) (str "Try '" program " --help' for more information."))
          2)

      (nil? from)
      (do ((:err io) (str program ": cannot read '" (:from parsed) "' as an instant"))
          ((:err io) "Use an ISO instant such as 2024-01-01T00:00:00Z.")
          2)

      :else
      (let [parsed-cron (try
                          {:ok (schedule/parse text)}
                          (catch clojure.lang.ExceptionInfo error
                            {:error (.getMessage error)}))]
        (if-let [message (:error parsed-cron)]
          (do ((:err io) (str program ": " message))
              ((:err io) (str "Try '" program " --help' for more information."))
              2)
          (let [parsed-schedule (:ok parsed-cron)
                runs (schedule/next-times parsed-schedule from (:count parsed))]
            (when (:explain parsed)
              (doseq [[label value] (explain-lines parsed-schedule)]
                ((:out io) (format "%-12s: %s" label value)))
              ((:out io) (str "next " (:count parsed) " run(s) after "
                              (schedule/format-instant from) ":")))
            (if (empty? runs)
              (do ((:err io) (str program ": '" (:spec parsed-schedule)
                                "' never fires (an impossible date)"))
                  1)
              (do (doseq [instant runs]
                    ((:out io) (schedule/format-instant instant)))
                  0))))))))

(defn run-command [args io]
  (let [parsed (options/parse args)]
    (case (:status parsed)
      :help (do ((:out io) (options/usage program)) 0)
      :version (do ((:out io) options/version) 0)
      :usage-error (do ((:err io) (str program ": " (:message parsed)))
                       ((:err io) (str "Try '" program " --help' for more information."))
                       2)
      :ok (run parsed io))))
