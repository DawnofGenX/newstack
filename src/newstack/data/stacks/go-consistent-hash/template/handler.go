package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const maxValueBytes = 64 * 1024

// Handler wraps a Cluster in an http.Handler with stable JSON output.
type Handler struct {
	c        *Cluster
	healthMu sync.Mutex
}

func NewHandler(c *Cluster) *Handler { return &Handler{c: c} }

// JSON shapes pinned as structs so field order is deterministic; the keys
// map is emitted through an ordered writer, never raw map iteration.
type healthResponse struct {
	Nodes    int             `json:"nodes"`
	Replicas int             `json:"replicas"`
	Points   int             `json:"points"`
	Keys     json.RawMessage `json:"keys"`
}

type errorResponse struct {
	Error  string `json:"error"`
	Key    string `json:"key,omitempty"`
	Detail string `json:"detail,omitempty"`
}

type ownersResponse struct {
	Key    string   `json:"key"`
	Owners []string `json:"owners"`
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	switch {
	case path == "/health":
		if r.Method != http.MethodGet {
			writeMethodNotAllowed(w)
			return
		}
		h.health(w)
	case path == "/_ring":
		if r.Method != http.MethodGet {
			writeMethodNotAllowed(w)
			return
		}
		h.ringOwners(w, r)
	case strings.HasPrefix(path, "/kv/"):
		key := strings.TrimPrefix(path, "/kv/")
		if key == "" || strings.Contains(key, "/") {
			writeNotFoundRoute(w, r)
			return
		}
		switch r.Method {
		case http.MethodPut:
			h.kvPut(w, r, key)
		case http.MethodGet:
			h.kvGet(w, key)
		case http.MethodDelete:
			h.kvDelete(w, key)
		default:
			writeMethodNotAllowed(w)
		}
	case strings.HasPrefix(path, "/_node/"):
		name := strings.TrimPrefix(path, "/_node/")
		if name == "" || strings.Contains(name, "/") {
			writeNotFoundRoute(w, r)
			return
		}
		switch r.Method {
		case http.MethodPut:
			h.nodeAdd(w, name)
		case http.MethodDelete:
			h.nodeDelete(w, name)
		default:
			writeMethodNotAllowed(w)
		}
	default:
		writeNotFoundRoute(w, r)
	}
}

func (h *Handler) health(w http.ResponseWriter) {
	counts, nodes, points := h.c.Health()
	h.healthMu.Lock()
	defer h.healthMu.Unlock()
	var b strings.Builder
	b.WriteString("{")
	names := make([]string, 0, len(counts))
	for k := range counts {
		names = append(names, k)
	}
	sort.Strings(names)
	for i, name := range names {
		if i > 0 {
			b.WriteString(",")
		}
		b.WriteString(strconv.Quote(name))
		b.WriteString(":")
		b.WriteString(strconv.Itoa(counts[name]))
	}
	b.WriteString("}")
	writeJSON(w, http.StatusOK, healthResponse{
		Nodes:    nodes,
		Replicas: h.c.ReplicaCount(),
		Points:   points,
		Keys:     json.RawMessage(b.String()),
	})
}

func (h *Handler) ringOwners(w http.ResponseWriter, r *http.Request) {
	key := r.URL.Query().Get("key")
	if key == "" {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "missing_key", Detail: "query param key is required"})
		return
	}
	owners := h.c.Owners(key)
	if owners == nil {
		owners = []string{}
	}
	writeJSON(w, http.StatusOK, ownersResponse{Key: key, Owners: owners})
}

func (h *Handler) kvPut(w http.ResponseWriter, r *http.Request, key string) {
	body, err := io.ReadAll(io.LimitReader(r.Body, maxValueBytes+1))
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: "read_failed"})
		return
	}
	if len(body) > maxValueBytes {
		writeJSON(w, http.StatusRequestEntityTooLarge, errorResponse{Error: "too_large", Detail: fmt.Sprintf("value exceeds %d bytes", maxValueBytes)})
		return
	}
	ttl := time.Duration(0)
	if t := r.URL.Query().Get("ttl"); t != "" {
		d, err := time.ParseDuration(t)
		if err != nil || d < 0 {
			writeJSON(w, http.StatusBadRequest, errorResponse{Error: "bad_ttl", Detail: t})
			return
		}
		ttl = d
	}
	owners := h.c.Put(key, string(body), ttl)
	writeJSON(w, http.StatusOK, ownersResponse{Key: key, Owners: owners})
}

func (h *Handler) kvGet(w http.ResponseWriter, key string) {
	v, node, ok := h.c.Get(key)
	if !ok {
		writeJSON(w, http.StatusNotFound, errorResponse{Error: "not_found", Key: key})
		return
	}
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Header().Set("X-Serving-Node", node)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(v))
}

func (h *Handler) kvDelete(w http.ResponseWriter, key string) {
	if h.c.Delete(key) {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	writeJSON(w, http.StatusNotFound, errorResponse{Error: "not_found", Key: key})
}

func (h *Handler) nodeAdd(w http.ResponseWriter, name string) {
	if !h.c.AddNode(name) {
		writeJSON(w, http.StatusConflict, errorResponse{Error: "duplicate_node", Detail: name})
		return
	}
	h.c.Rebalance("", name)
	writeJSON(w, http.StatusCreated, ownersResponse{Key: name, Owners: []string{name}})
}

func (h *Handler) nodeDelete(w http.ResponseWriter, name string) {
	if !h.c.RemoveNode(name) {
		writeJSON(w, http.StatusNotFound, errorResponse{Error: "unknown_node", Detail: name})
		return
	}
	writeJSON(w, http.StatusOK, ownersResponse{Key: name, Owners: []string{}})
}

func writeJSON(w http.ResponseWriter, code int, payload any) {
	buf := &strings.Builder{}
	enc := json.NewEncoder(buf)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(payload)
	body := strings.TrimSuffix(buf.String(), "\n")
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_, _ = w.Write([]byte(body))
}

func writeMethodNotAllowed(w http.ResponseWriter) {
	writeJSON(w, http.StatusMethodNotAllowed, errorResponse{Error: "method_not_allowed"})
}

func writeNotFoundRoute(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusNotFound, errorResponse{Error: "not_found", Detail: fmt.Sprintf("no route for %s %s", r.Method, r.URL.Path)})
}
