(ns edncli.cli
  (:require [edncli.core :as core]
            [clojure.string :as str]))

(def program "{{ npm_name }}")

(defn- read-input [path io]
  (if (or (nil? path) (= path "-"))
    (let [sb (StringBuilder.)]
      (loop []
        (let [line (.readLine *in*)]
          (when line
            (.append sb line)
            (.append sb "\n")
            (recur))))
      [true (str sb)])
    (let [f (java.io.File. path)]
      (if (.exists f)
        (try [true (slurp f)]
             (catch Exception e [false (.getMessage e)]))
        [false (str "no such file: " path)]))))

(defn- run-pretty [args io]
  (let [path (first args)
        [ok text] (read-input path io)]
    (if-not ok
      (do ((:err io) (str program ": " text)) 1)
      (let [[rok value] (core/read-edn text)]
        (if-not rok
          (do ((:err io) (str program ": " value)) 1)
          (do ((:out io) (str/trimr (core/pretty value))) 0))))))

(defn- run-get [args io]
  (if (< (count args) 1)
    (do ((:err io) (str program ": missing path")) 2)
    (let [path (first args)
          file (second args)
          [ok text] (read-input file io)]
      (if-not ok
        (do ((:err io) (str program ": " text)) 1)
        (let [[rok value] (core/read-edn text)]
          (if-not rok
            (do ((:err io) (str program ": " value)) 1)
            (let [v (core/get-at value path)]
              (if (nil? v)
                (do ((:err io) (str program ": not found: " path)) 1)
                (do ((:out io) (pr-str v)) 0)))))))))

(defn- run-keys [args io]
  (let [path (first args)
        [ok text] (read-input path io)]
    (if-not ok
      (do ((:err io) (str program ": " text)) 1)
      (let [[rok value] (core/read-edn text)]
        (if-not rok
          (do ((:err io) (str program ": " value)) 1)
          (do (doseq [k (core/top-keys value)] ((:out io) (pr-str k))) 0))))))

(defn- run-validate [args io]
  (let [path (first args)
        [ok text] (read-input path io)]
    (if-not ok
      (do ((:err io) (str program ": " text)) 1)
      (let [[rok _] (core/read-edn text)]
        (if rok 0 (do ((:err io) (str program ": invalid EDN")) 1))))))

(defn run [args io]
  (let [args (vec args)]
    (cond
      (or (empty? args) (= (first args) "pretty"))
      (run-pretty (if (empty? args) [] (rest args)) io)
      (= (first args) "get") (run-get (rest args) io)
      (= (first args) "keys") (run-keys (rest args) io)
      (= (first args) "validate") (run-validate (rest args) io)
      (or (= (first args) "-h") (= (first args) "--help")) (do ((:out io) (str "Usage: " program " [pretty|get PATH|keys|validate] [FILE]\n")) 0)
      (or (= (first args) "-V") (= (first args) "--version")) (do ((:out io) "0.1.0") 0)
      :else (do ((:err io) (str program ": unknown command: " (first args)))
                ((:err io) (str "Try '" program " --help' for more information."))
                2))))