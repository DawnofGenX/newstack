(ns {{ package_name }}.counts)

;; The counting rules, with no HTTP in sight. `lines` ends at every newline,
;; `words` is a maximal run of non-space characters and `bytes` is the UTF-8
;; length, so the figures match `wc` for the same text.

(def empty-counts {:lines 0 :words 0 :bytes 0})

(defn count-text
  "Count a string. Throws when handed something that is not text."
  [text]
  (when-not (string? text)
    (throw (IllegalArgumentException.
            (str "count-text expects a string, got " (.getName (class text))))))
  {:lines (count (filter #(= % \newline) text))
   :words (count (re-seq #"\S+" text))
   :bytes (alength (.getBytes ^String text "UTF-8"))})

(defn counted-json
  "The response body for a successful count: the text that was counted, plus figures."
  [text]
  (merge {:text text} (count-text text)))
