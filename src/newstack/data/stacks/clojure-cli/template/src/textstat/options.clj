(ns textstat.options
  (:require [textstat.counts :as counts]))

(def version "0.1.0")

(defn usage [program]
  (str "Usage: " program " [-l] [-w] [-c] [FILE...]\n"
       "\n"
       "Print newline, word and byte counts for each FILE, and a total line if\n"
       "more than one FILE is given. With no FILE, or when FILE is -, read\n"
       "standard input. With no flag, all three figures are printed.\n"
       "\n"
       "  -l, --lines   print the newline count\n"
       "  -w, --words   print the word count\n"
       "  -c, --bytes   print the byte count\n"
       "  -h, --help    print this help and exit\n"
       "  -V, --version print the version and exit\n"))

(defn- append-flag [figures flag]
  (case flag
    \l (assoc figures :lines true)
    \w (assoc figures :words true)
    \c (assoc figures :bytes true)
    nil))

;; Fold the short flags of one argument (`-lw`, or `-w` alone). Returns the
;; updated figures on success, or the error message on an unknown flag.
(defn- short-flags [figures arg]
  (reduce (fn [acc flag]
            (if (string? acc)
              acc
              (let [updated (append-flag acc flag)]
                (if updated updated (str "unknown option: -" flag)))))
    figures
    (subs arg 1)))

;; Returns the updated figures on success, or the error message otherwise.
(defn- long-flag [figures arg]
  (case arg
    "--lines" (assoc figures :lines true)
    "--words" (assoc figures :words true)
    "--bytes" (assoc figures :bytes true)
    (str "unknown option: " arg)))

(defn- parse-loop [remaining figures files only-files]
  (if (empty? remaining)
    (let [chosen (if (= figures counts/no-figures) counts/all-figures figures)]
      {:figures chosen :files files :status :ok})
    (let [arg (first remaining)
          rest (rest remaining)]
      (cond
        only-files
        (parse-loop rest figures (conj files arg) true)
        (= arg "--")
        (parse-loop rest figures files true)
        (or (= arg "-h") (= arg "--help"))
        {:figures figures :files [] :status :help}
        (or (= arg "-V") (= arg "--version"))
        {:figures figures :files [] :status :version}
        (.startsWith arg "--")
        (let [result (long-flag figures arg)]
          (if (map? result)
            (parse-loop rest result files false)
            {:figures figures :files files :status :usage-error :message result}))
        (and (.startsWith arg "-") (> (count arg) 1))
        (let [result (short-flags figures arg)]
          (if (map? result)
            (parse-loop rest result files false)
            {:figures figures :files files :status :usage-error :message result}))
        :else
        (parse-loop rest figures (conj files arg) false)))))

;; Parse argv into a decision: what to print, what to read, and whether to run.
(defn parse [args]
  (parse-loop (vec args) counts/no-figures [] false))
