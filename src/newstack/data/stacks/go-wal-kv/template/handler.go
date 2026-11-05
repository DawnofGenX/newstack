package main

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"
	"strings"
)

const maxBodyBytes = 64 << 10

// apiError is the body every refusal uses.
type apiError struct {
	Error  string `json:"error"`
	Detail string `json:"detail,omitempty"`
	Key    string `json:"key,omitempty"`
}

// healthBody pins the field order the tests and the smoke script expect.
type healthBody struct {
	Status string `json:"status"`
	Keys   int    `json:"keys"`
}

type compactBody struct {
	Before  int `json:"before"`
	After   int `json:"after"`
	Records int `json:"records"`
}

type storedBody struct {
	Status string `json:"status"`
	Key    string `json:"key"`
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	payload, err := json.Marshal(body)
	if err != nil {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusInternalServerError)
		io.WriteString(w, `{"error":"encode_failed"}`)
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Content-Length", strconv.Itoa(len(payload)))
	w.WriteHeader(status)
	w.Write(payload)
}

// newHandler wires the routes; every route answers a JSON body of its own so
// Go's default 404/405 pages never leak into the contract.
func newHandler(store *Store) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path
		switch {
		case path == "/health":
			if !allow(w, r, http.MethodGet) {
				return
			}
			stats := store.Stats()
			writeJSON(w, http.StatusOK, healthBody{Status: "ok", Keys: stats.Keys})
		case path == "/wal":
			if !allow(w, r, http.MethodGet) {
				return
			}
			writeJSON(w, http.StatusOK, store.Stats())
		case path == "/compact":
			if !allow(w, r, http.MethodPost) {
				return
			}
			before, after, err := store.Compact()
			if err != nil {
				writeJSON(w, http.StatusInternalServerError, apiError{Error: "compact_failed", Detail: err.Error()})
				return
			}
			writeJSON(w, http.StatusOK, compactBody{Before: before, After: after, Records: after})
		case strings.HasPrefix(path, "/kv/"):
			key := strings.TrimPrefix(path, "/kv/")
			if key == "" {
				writeJSON(w, http.StatusNotFound, apiError{Error: "not_found", Detail: "no key in the path"})
				return
			}
			handleKey(w, r, store, key)
		default:
			writeJSON(w, http.StatusNotFound, apiError{
				Error:  "not_found",
				Detail: "no route for " + r.Method + " " + path,
			})
		}
	})
}

func allow(w http.ResponseWriter, r *http.Request, method string) bool {
	if r.Method == method {
		return true
	}
	writeJSON(w, http.StatusMethodNotAllowed, apiError{Error: "method_not_allowed"})
	return false
}

func handleKey(w http.ResponseWriter, r *http.Request, store *Store, key string) {
	if len(key) > maxKeyLength {
		writeJSON(w, http.StatusBadRequest, apiError{Error: "invalid_key", Detail: "a key is at most 256 bytes"})
		return
	}
	switch r.Method {
	case http.MethodGet:
		value, ok := store.Get(key)
		if !ok {
			writeJSON(w, http.StatusNotFound, apiError{Error: "not_found", Key: key})
			return
		}
		w.Header().Set("Content-Type", "application/octet-stream")
		w.Header().Set("Content-Length", strconv.Itoa(len(value)))
		w.WriteHeader(http.StatusOK)
		w.Write(value)
	case http.MethodPut:
		value, err := readBody(r)
		if err != nil {
			if errors.Is(err, errTooLarge) {
				writeJSON(w, http.StatusRequestEntityTooLarge, apiError{Error: "value_too_large"})
				return
			}
			writeJSON(w, http.StatusBadRequest, apiError{Error: "read_failed", Detail: err.Error()})
			return
		}
		if err := store.Put(key, value); err != nil {
			writeJSON(w, http.StatusInternalServerError, apiError{Error: "write_failed", Detail: err.Error()})
			return
		}
		writeJSON(w, http.StatusCreated, storedBody{Status: "stored", Key: key})
	case http.MethodDelete:
		removed, err := store.Delete(key)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, apiError{Error: "delete_failed", Detail: err.Error()})
			return
		}
		if !removed {
			writeJSON(w, http.StatusNotFound, apiError{Error: "not_found", Key: key})
			return
		}
		w.WriteHeader(http.StatusNoContent)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, apiError{Error: "method_not_allowed"})
	}
}

var errTooLarge = errors.New("body too large")

// readBody enforces the cap while the bytes arrive, not after them: a client
// that streams a gigabyte must be cut off, not buffered.
func readBody(r *http.Request) ([]byte, error) {
	if r.ContentLength > maxBodyBytes {
		return nil, errTooLarge
	}
	// Read one byte past the cap: that is enough to know the body is too big
	// without buffering the rest of it.
	buffer, err := io.ReadAll(io.LimitReader(r.Body, maxBodyBytes+1))
	if err != nil {
		return nil, err
	}
	if len(buffer) > maxBodyBytes {
		return nil, errTooLarge
	}
	return buffer, nil
}
