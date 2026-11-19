(ns edncli.main
  (:require [edncli.cli :as cli]))

(defn -main [& args]
  (let [io {:in *in* :out #(println %) :err #(binding [*out* *err*] (println %))}]
    (System/exit (cli/run args io))))