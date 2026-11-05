(ns {{ package_name }}.handler
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [ring.util.codec :as codec]
            [{{ package_name }}.counts :refer [counted-json]]))

;; A plain Ring handler: a request map in, a response map out. Nothing here needs
;; a socket, so the tests call it directly; `server.clj` is the only file that
;; knows a port exists.

(def json-headers {"content-type" "application/json; charset=utf-8"})

(defn- respond [status body]
  {:status status :headers json-headers :body (json/generate-string body)})

(defn- not-found [request]
  (respond 404 {:error "not_found"
                :detail (str "no route for " (str/upper-case (name (:request-method request)))
                             " " (:uri request))}))

(defn- query-text [request]
  (let [params (codec/form-decode-map (or (:query-string request) ""))]
    (when (contains? params "text")
      (get params "text"))))

(defn- posted-text [request]
  (let [body (try
               (json/parse-string (slurp (:body request)))
               (catch Exception _ ::invalid))]
    (if (= body ::invalid)
      ::invalid
      (get body "text"))))

(defn- stats-response [text]
  (if (string? text)
    (respond 200 (counted-json text))
    (respond 422 {:error "missing_text"})))

(defn handler [request]
  (let [method (:request-method request)]
    (case [method (:uri request)]
      [:get "/health"] (respond 200 {:status "ok"})
      [:get "/stats"] (stats-response (query-text request))
      [:post "/stats"] (let [text (posted-text request)]
                         (if (= text ::invalid)
                           (respond 422 {:error "invalid_json"})
                           (stats-response text)))
      (if (contains? #{[:head "/health"] [:head "/stats"] [:put "/stats"]} [method (:uri request)])
        (respond 405 {:error "method_not_allowed"})
        (not-found request)))))
