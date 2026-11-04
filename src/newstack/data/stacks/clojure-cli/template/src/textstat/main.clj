(ns textstat.main
  (:require [textstat.cli :as cli]))

;; The only namespace that touches the real file system, the real terminal and
;; the real exit status.
(defn- system-io []
  {:read-file (fn [path]
                (try
                  [true (java.nio.file.Files/readAllBytes
                          (.toPath (java.io.File. path)))]
                  (catch Exception _
                    [false (str "cannot open '" path "'")])))
   :read-stdin (fn []
                 ;; `*in*` is a LineNumberingPushbackReader, which has no
                 ;; readAllBytes; the byte stream behind it does.
                 (.readAllBytes (java.lang.System/in)))
   :out (fn [line] (println line))
   :err (fn [line] (binding [*out* *err*] (println line)))})

(defn -main [& args]
  (let [code (cli/run (vec args) (system-io))]
    (System/exit code)))
