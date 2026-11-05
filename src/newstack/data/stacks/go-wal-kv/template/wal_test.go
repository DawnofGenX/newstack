package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func newStore(t *testing.T) *Store {
	t.Helper()
	store, err := Open(filepath.Join(t.TempDir(), "log"))
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	t.Cleanup(func() { store.Close() })
	return store
}

func TestRecordRoundTrip(t *testing.T) {
	frame, err := encodeRecord(OpPut, "greeting", []byte("hello"))
	if err != nil {
		t.Fatalf("encode: %v", err)
	}
	record, size, err := readRecord(bytes.NewReader(frame))
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if record.Op != OpPut || record.Key != "greeting" || !bytes.Equal(record.Value, []byte("hello")) {
		t.Fatalf("unexpected record: %+v", record)
	}
	if size != int64(len(frame)) {
		t.Fatalf("size %d, want %d", size, len(frame))
	}
}

func TestBadFrames(t *testing.T) {
	frame, _ := encodeRecord(OpPut, "k", []byte("value"))
	if _, _, err := readRecord(bytes.NewReader(frame[:5])); !errors.Is(err, ErrTorn) {
		t.Fatalf("short header: %v", err)
	}
	if _, _, err := readRecord(bytes.NewReader(frame[:len(frame)-1])); !errors.Is(err, ErrTorn) {
		t.Fatalf("short body: %v", err)
	}
	flipped := append([]byte(nil), frame...)
	flipped[len(flipped)-1] ^= 0x7F
	if _, _, err := readRecord(bytes.NewReader(flipped)); !errors.Is(err, ErrCorrupt) {
		t.Fatalf("flipped byte: %v", err)
	}
	if _, err := encodeRecord(OpPut, "", nil); err == nil {
		t.Fatal("an empty key must be refused")
	}
	if _, err := encodeRecord(OpPut, strings.Repeat("k", maxKeyLength+1), nil); err == nil {
		t.Fatal("an over-long key must be refused")
	}
}

func TestStoreSurvivesReopen(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "log")
	store, err := Open(dir)
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	if err := store.Put("a", []byte("one")); err != nil {
		t.Fatalf("put: %v", err)
	}
	if err := store.Put("b", []byte("two")); err != nil {
		t.Fatalf("put: %v", err)
	}
	if _, err := store.Delete("a"); err != nil {
		t.Fatalf("delete: %v", err)
	}
	store.Close()

	again, err := Open(dir)
	if err != nil {
		t.Fatalf("reopen: %v", err)
	}
	defer again.Close()
	if _, ok := again.Get("a"); ok {
		t.Fatal("the tombstone did not survive")
	}
	value, ok := again.Get("b")
	if !ok || string(value) != "two" {
		t.Fatalf("b: %q %v", value, ok)
	}
}

func TestTornTailIsTruncated(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "log")
	store, err := Open(dir)
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	store.Put("kept", []byte("value"))
	store.Close()

	segment := segmentPath(dir, 1)
	file, err := os.OpenFile(segment, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		t.Fatalf("open segment: %v", err)
	}
	if _, err := file.Write([]byte{0, 0, 0, 9, 1}); err != nil {
		t.Fatalf("append: %v", err)
	}
	file.Close()

	again, err := Open(dir)
	if err != nil {
		t.Fatalf("reopen: %v", err)
	}
	defer again.Close()
	if !again.Recovery().TornTail {
		t.Fatal("the torn tail was not reported")
	}
	if _, ok := again.Get("kept"); !ok {
		t.Fatal("the torn tail destroyed a good record")
	}
}

func TestCompaction(t *testing.T) {
	store := newStore(t)
	for index := 0; index < 10; index++ {
		store.Put(strings.Repeat("k", index+1), []byte("value"))
	}
	for index := 0; index < 4; index++ {
		store.Delete(strings.Repeat("k", index+1))
	}
	written, after, err := store.Compact()
	if err != nil {
		t.Fatalf("compact: %v", err)
	}
	if written != 14 || after != 6 {
		t.Fatalf("before %d after %d, want 14 and 6", written, after)
	}
	if store.Stats().Segments != 1 {
		t.Fatalf("segments %d", store.Stats().Segments)
	}
	if _, ok := store.Get("kkkkk"); !ok {
		t.Fatal("compaction dropped a live key")
	}
}

func TestSegmentIndexesSkipTemporaries(t *testing.T) {
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "wal-000001.log"), nil, 0o644)
	os.WriteFile(filepath.Join(dir, "wal-000003.log"), nil, 0o644)
	os.WriteFile(filepath.Join(dir, "wal-000004.log.tmp"), nil, 0o644)
	os.WriteFile(filepath.Join(dir, "notes.txt"), nil, 0o644)
	indexes, err := segmentIndexes(dir)
	if err != nil {
		t.Fatalf("indexes: %v", err)
	}
	if len(indexes) != 2 || indexes[0] != 1 || indexes[1] != 3 {
		t.Fatalf("indexes %v", indexes)
	}
}

func TestParsePort(t *testing.T) {
	if port, err := parsePort("8080"); err != nil || port != 8080 {
		t.Fatalf("8080: %d %v", port, err)
	}
	for _, bad := range []string{"", "abc", "-1", "70000"} {
		if _, err := parsePort(bad); err == nil {
			t.Fatalf("%q was accepted", bad)
		}
	}
}

func apiRequest(t *testing.T, handler http.Handler, method, target string, body []byte) (int, string) {
	t.Helper()
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		reader = bytes.NewReader(body)
	}
	request := httptest.NewRequest(method, target, reader)
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)
	return recorder.Code, recorder.Body.String()
}

func TestHTTPContract(t *testing.T) {
	store := newStore(t)
	handler := newHandler(store)

	status, body := apiRequest(t, handler, http.MethodGet, "/health", nil)
	if status != 200 || !strings.Contains(body, `"keys":0`) {
		t.Fatalf("health: %d %s", status, body)
	}
	status, body = apiRequest(t, handler, http.MethodPut, "/kv/greeting", []byte("hello"))
	if status != 201 || !strings.Contains(body, `"key":"greeting"`) {
		t.Fatalf("put: %d %s", status, body)
	}
	status, body = apiRequest(t, handler, http.MethodGet, "/kv/greeting", nil)
	if status != 200 || body != "hello" {
		t.Fatalf("get: %d %q", status, body)
	}
	status, _ = apiRequest(t, handler, http.MethodGet, "/kv/missing", nil)
	if status != 404 {
		t.Fatalf("missing: %d", status)
	}
	status, _ = apiRequest(t, handler, http.MethodPatch, "/kv/greeting", nil)
	if status != 405 {
		t.Fatalf("patch: %d", status)
	}
	status, _ = apiRequest(t, handler, http.MethodDelete, "/kv/greeting", nil)
	if status != 204 {
		t.Fatalf("delete: %d", status)
	}
	status, body = apiRequest(t, handler, http.MethodGet, "/kv/"+strings.Repeat("k", maxKeyLength+1), nil)
	if status != 400 || !strings.Contains(body, "invalid_key") {
		t.Fatalf("long key: %d %s", status, body)
	}
}

func TestHTTPBodyLimit(t *testing.T) {
	handler := newHandler(newStore(t))
	status, body := apiRequest(t, handler, http.MethodPut, "/kv/big", bytes.Repeat([]byte("x"), maxBodyBytes+1))
	if status != 413 || !strings.Contains(body, "value_too_large") {
		t.Fatalf("big body: %d %s", status, body)
	}
}

func TestHTTPStatsAreJSON(t *testing.T) {
	store := newStore(t)
	store.Put("one", []byte("1"))
	handler := newHandler(store)
	status, body := apiRequest(t, handler, http.MethodGet, "/wal", nil)
	if status != 200 {
		t.Fatalf("wal: %d", status)
	}
	var stats Stats
	if err := json.Unmarshal([]byte(body), &stats); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if stats.Keys != 1 || stats.Records != 1 {
		t.Fatalf("stats %+v", stats)
	}
}
