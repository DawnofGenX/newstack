package main

import (
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
)

var hopHeaders = []string{
	"Connection",
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Te",
	"Trailers",
	"Transfer-Encoding",
	"Upgrade",
}

func NewProxy(upstream string) http.Handler {
	target, err := url.Parse(upstream)
	if err != nil {
		panic(err)
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		for _, h := range hopHeaders {
			req.Header.Del(h)
		}
		clientIP := req.RemoteAddr
		if host, _, err := net.SplitHostPort(clientIP); err == nil {
			clientIP = host
		}
		if prior := req.Header.Get("X-Forwarded-For"); prior != "" {
			req.Header.Set("X-Forwarded-For", prior+", "+clientIP)
		} else {
			req.Header.Set("X-Forwarded-For", clientIP)
		}
	}
	proxy.ModifyResponse = func(resp *http.Response) error {
		for _, h := range hopHeaders {
			resp.Header.Del(h)
		}
		return nil
	}
	return proxy
}

func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5541"
	}
	if _, err := strconv.Atoi(port); err != nil {
		port = "5541"
	}
	upstream := os.Getenv("UPSTREAM")
	if upstream == "" {
		upstream = "http://127.0.0.1:5542"
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	mux.Handle("/", NewProxy(upstream))
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		panic(err)
	}
}
