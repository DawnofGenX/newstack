(ns cronkit.options)

(def version "0.1.0")

(defn usage [program]
  (str "Usage: " program " [options] EXPRESSION\n"
       "\n"
       "Print the next times a five field cron expression fires, in UTC.\n"
       "EXPRESSION is the usual 'minute hour day-of-month month day-of-week'.\n"
       "Quote it, or pass the five fields as separate arguments.\n"
       "\n"
       "  -n, --count N   how many runs to print (default 5)\n"
       "      --from ISO  start searching after this instant (default: now)\n"
       "      --explain   also print what each field means\n"
       "  -h, --help      print this help and exit\n"
       "  -V, --version   print the version and exit\n"
       "\n"
       "Fields accept '*', numbers, names (JAN, MON), lists (1,15), ranges\n"
       "(1-5) and steps (*/15, 1-59/2). Exit codes: 0 ok, 1 the expression can\n"
       "never fire, 2 bad usage.\n"))

(defn- parse-loop [remaining options operands]
  (if (empty? remaining)
    (assoc options :operands operands :status :ok)
    (let [arg (first remaining)
          rest-args (rest remaining)]
      (cond
        (= arg "--") (parse-loop (vec rest-args) options operands)

        (or (= arg "-h") (= arg "--help")) (assoc options :status :help)

        (or (= arg "-V") (= arg "--version")) (assoc options :status :version)

        (or (= arg "-n") (= arg "--count"))
        (let [value (first rest-args)]
          (cond
            (nil? value) (assoc options :status :usage-error :message (str arg " needs a value"))
            (not (re-matches #"\d+" value))
            (assoc options :status :usage-error
                   :message (str "count must be a number, got '" value "'"))
            (zero? (parse-long value))
            (assoc options :status :usage-error :message "count must be positive")
            :else (parse-loop (vec (rest rest-args)) (assoc options :count (parse-long value)) operands)))

        (= arg "--from")
        (let [value (first rest-args)]
          (if (nil? value)
            (assoc options :status :usage-error :message "--from needs an instant")
            (parse-loop (vec (rest rest-args)) (assoc options :from value) operands)))

        (= arg "--explain") (parse-loop (vec rest-args) (assoc options :explain true) operands)

        (.startsWith arg "-") (assoc options :status :usage-error
                                     :message (str "unknown option: " arg))

        :else (parse-loop (vec rest-args) options (conj operands arg))))))

(defn parse [args]
  (parse-loop (vec args) {:count 5 :explain false} []))
