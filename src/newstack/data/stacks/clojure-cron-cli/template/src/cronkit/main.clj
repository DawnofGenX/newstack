(ns cronkit.main
  (:require [cronkit.cli :as cli]))

(defn- system-io []
  {:out (fn [line] (println line))
   :err (fn [line] (binding [*out* *err*] (println line)))})

(defn -main [& args]
  (System/exit (cli/run-command (vec args) (system-io))))
