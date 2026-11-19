(ns edncli.core
  (:require [clojure.edn :as edn]
            [clojure.pprint :as pp]
            [clojure.string :as str]))

(defn read-edn
  "Read EDN from a string. Returns [ok value-or-error]."
  [s]
  (try
    [true (edn/read-string s)]
    (catch Exception e
      [false (.getMessage e)])))

(defn parse-path
  "Turn a slash-separated path like ':a/:b' or 'a/b' into keywords."
  [p]
  (->> (str/split p #"/")
       (remove str/blank?)
       (mapv (fn [x] (if (.startsWith x ":") (keyword (subs x 1)) (keyword x))))))

(defn get-at [value path]
  (get-in value (parse-path path)))

(defn pretty [value]
  (with-out-str (pp/pprint value)))

(defn top-keys [value]
  (cond
    (map? value) (keys value)
    (vector? value) (range (count value))
    :else nil))