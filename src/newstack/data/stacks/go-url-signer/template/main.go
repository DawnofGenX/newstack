package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"
)

func main() {
	mode := flag.String("mode", "sign", "sign or serve")
	secret := flag.String("secret", "", "hmac secret (or SIGNING_SECRET)")
	path := flag.String("path", "/", "path to sign")
	method := flag.String("method", "GET", "http method to sign")
	ttl := flag.Duration("ttl", time.Minute, "signature lifetime")
	addr := flag.String("addr", "", "listen address for serve mode (default :$PORT)")
	flag.Parse()

	key := *secret
	if key == "" {
		key = os.Getenv("SIGNING_SECRET")
	}
	if key == "" {
		fmt.Fprintln(os.Stderr, "a secret is required via -secret or SIGNING_SECRET")
		os.Exit(2)
	}
	signer := URLSigner{Secret: []byte(key)}

	switch *mode {
	case "sign":
		signed, err := signer.SignedURL(*method, *path, *ttl)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(signed)
	case "serve":
		listen := *addr
		if listen == "" {
			listen = ":" + os.Getenv("PORT")
			if os.Getenv("PORT") == "" {
				listen = ":8080"
			}
		}
		mux := http.NewServeMux()
		mux.Handle("/files/", signer.Handler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprintf(w, "ok %s\n", r.URL.Path)
		})))
		fmt.Fprintf(os.Stderr, "listening on %s\n", listen)
		if err := http.ListenAndServe(listen, mux); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "unknown mode %q\n", *mode)
		os.Exit(2)
	}
}
