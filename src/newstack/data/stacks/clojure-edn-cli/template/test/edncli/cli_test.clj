(ns edncli.cli-test
  (:require [clojure.test :refer [deftest is]]
            [edncli.cli :as cli]))

(defn- mkio []
  (let [out (java.io.StringWriter.)
        err (java.io.StringWriter.)]
    {:in nil
     :out (fn [s] (.write out (str s "\n")))
     :err (fn [s] (.write err (str s "\n")))
     :outw out :errw err}))

(deftest help-exit
  (let [io (mkio)]
    (is (= 0 (cli/run ["--help"] io)))))

(deftest usage-error-exit
  (let [io (mkio)]
    (is (= 2 (cli/run ["frobnicate"] io)))))

(deftest pretty-stdin
  (let [io (mkio)]
    (with-in-str "{:a 1}"
      (is (= 0 (cli/run ["pretty" "-"] (assoc io :in *in*)))))))