(ns {{ package_name }}.handler-test
  (:require [cheshire.core :as json]
            [clojure.test :refer [deftest is testing]]
            [ring.mock.request :as mock]
            [{{ package_name }}.handler :refer [handler]]))

(defn- body [response]
  (json/parse-string (:body response)))

(deftest health
  (let [response (handler (mock/request :get "/health"))]
    (is (= 200 (:status response)))
    (is (= {"status" "ok"} (body response)))
    (is (= "application/json; charset=utf-8" (get-in response [:headers "content-type"])))))

(deftest counts-the-query-parameter
  (let [response (handler (mock/request :get "/stats" {:text "hello world\n"}))]
    (is (= 200 (:status response)))
    (is (= {"text" "hello world\n" "lines" 1 "words" 2 "bytes" 12} (body response)))))

(deftest an-empty-parameter-is-empty-text
  (let [response (handler (mock/request :get "/stats" {:text ""}))]
    (is (= 200 (:status response)))
    (is (= {"text" "" "lines" 0 "words" 0 "bytes" 0} (body response)))))

(deftest a-missing-parameter-is-a-422
  (let [response (handler (mock/request :get "/stats"))]
    (is (= 422 (:status response)))
    (is (= {"error" "missing_text"} (body response)))))

(deftest counts-a-posted-body
  (let [response (handler (-> (mock/request :post "/stats")
                              (mock/json-body {"text" "a b\nc\n"})))]
    (is (= 200 (:status response)))
    (is (= {"text" "a b\nc\n" "lines" 2 "words" 3 "bytes" 6} (body response)))))

(deftest padding-survives-the-round-trip
  (let [response (handler (-> (mock/request :post "/stats")
                              (mock/json-body {"text" "  padded  \n"})))]
    (is (= {"text" "  padded  \n" "lines" 1 "words" 1 "bytes" 11} (body response)))))

(deftest a-body-that-is-not-json-is-a-422
  (let [response (handler (-> (mock/request :post "/stats")
                              (mock/content-type "application/json")
                              (mock/body "not json")))]
    (is (= 422 (:status response)))
    (is (= {"error" "invalid_json"} (body response)))))

(deftest non-string-text-is-a-422
  (let [response (handler (-> (mock/request :post "/stats")
                              (mock/json-body {"text" 42})))]
    (is (= 422 (:status response)))
    (is (= {"error" "missing_text"} (body response)))))

(deftest an-unknown-route-is-a-json-404
  (let [response (handler (mock/request :get "/nope"))]
    (is (= 404 (:status response)))
    (is (= {"error" "not_found" "detail" "no route for GET /nope"} (body response)))))
