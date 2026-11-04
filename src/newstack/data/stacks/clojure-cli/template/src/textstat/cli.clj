(ns textstat.cli
  (:require [textstat.counts :as counts]
            [textstat.options :as options]))

(def program "{{ npm_name }}")

;; The `:ok` branch: read every operand, tally the readable ones, print one
;; right-aligned row per file plus a `total` row when there is more than one
;; operand, and return 0 (all readable) or 1 (something could not be opened).
(defn- run-ok [paths figures io]
  (let [results (mapv (fn [path]
                        (if (= path "-")
                          [true (counts/of-bytes ((:read-stdin io))) "-"]
                          (let [r ((:read-file io) path)]
                            (if (first r)
                              [true (counts/of-bytes (second r)) path]
                              [false (second r) path]))))
                      paths)
        failures (filterv (complement first) results)
        rows (filterv first results)
        total (if (> (count paths) 1)
                [true (reduce (fn [acc [_ c _]] (counts/add acc c))
                              counts/empty-counts
                              rows)
                 "total"]
                nil)
        shown (if total (conj rows total) rows)
        width (counts/width (mapv second shown) figures)]
    (doseq [[_ msg _] failures]
      ((:err io) (str "error: " msg)))
    (doseq [[_ c label] shown]
      ((:out io) (counts/format-row figures c label width)))
    (if (empty? failures) 0 1)))

;; The whole program as a pure-ish function: argv plus an io record in, an exit
;; code out. Only `main` turns that code into a real `System/exit`.
(defn run [args io]
  (let [parsed (options/parse args)]
    (case (:status parsed)
      :help
      (do ((:out io) (options/usage program)) 0)
      :version
      (do ((:out io) options/version) 0)
      :usage-error
      (do ((:err io) (str program ": " (:message parsed)))
          ((:err io) (str "Try '" program "' --help for more information."))
          2)
      :ok
      (let [paths (if (empty? (:files parsed)) ["-"] (:files parsed))]
        (run-ok paths (:figures parsed) io)))))
