(ns {{ package_name }}.server
  (:require [ring.adapter.jetty :refer [run-jetty]]
            [{{ package_name }}.handler :refer [handler]])
  (:gen-class))

(defn -main [& _]
  (let [port (Integer/parseInt (or (System/getenv "PORT") "8080"))]
    (println (str "listening on http://127.0.0.1:" port))
    (run-jetty handler {:port port :join? true})))
