package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type checker struct {
	checks  int
	failed  int
	verbose bool
}

func (c *checker) that(name string, ok bool, detail string) {
	c.checks++
	if ok {
		if c.verbose {
			fmt.Printf("ok %d - %s\n", c.checks, name)
		}
		return
	}
	c.failed++
	if detail != "" {
		fmt.Printf("FAIL %d - %s: %s\n", c.checks, name, detail)
		return
	}
	fmt.Printf("FAIL %d - %s\n", c.checks, name)
}

func (c *checker) equal(name string, got, want any) {
	c.that(name, fmt.Sprint(got) == fmt.Sprint(want), fmt.Sprintf("got %v, want %v", got, want))
}

func (c *checker) same(name string, got, want []byte) {
	c.that(name, bytes.Equal(got, want), fmt.Sprintf("got %q, want %q", got, want))
}

func runSelftest() int {
	c := &checker{verbose: true}

	// -- the frame itself -------------------------------------------------
	frame, err := encodeRecord(OpPut, "alpha", []byte("one"))
	c.that("a record encodes", err == nil, fmt.Sprint(err))

	record, size, err := readRecord(bytes.NewReader(frame))
	c.equal("the record reads back", record.Key, "alpha")
	c.same("the value reads back", record.Value, []byte("one"))
	c.equal("the op reads back", record.Op, OpPut)
	c.equal("the frame size is reported", size, int64(len(frame)))

	tombstone, err := encodeRecord(OpDelete, "alpha", nil)
	c.that("a tombstone encodes", err == nil, fmt.Sprint(err))
	deleted, _, err := readRecord(bytes.NewReader(tombstone))
	c.equal("the tombstone op reads back", deleted.Op, OpDelete)

	_, _, err = readRecord(bytes.NewReader(frame[:6]))
	c.that("a short header is torn", errors.Is(err, ErrTorn), fmt.Sprint(err))
	_, _, err = readRecord(bytes.NewReader(frame[:len(frame)-2]))
	c.that("a short payload is torn", errors.Is(err, ErrTorn), fmt.Sprint(err))

	broken := append([]byte(nil), frame...)
	broken[9] ^= 0xFF
	_, _, err = readRecord(bytes.NewReader(broken))
	c.that("a flipped payload byte is corrupt", errors.Is(err, ErrCorrupt), fmt.Sprint(err))

	_, err = encodeRecord(OpPut, "", nil)
	c.that("an empty key is refused", err != nil, "encode accepted an empty key")
	longKey := strings.Repeat("k", maxKeyLength+1)
	_, err = encodeRecord(OpPut, longKey, nil)
	c.that("an over-long key is refused", err != nil, "encode accepted a 257 byte key")

	// -- the store --------------------------------------------------------
	dir := filepath.Join(mustTempDir(c), "log")
	store, err := Open(dir)
	c.that("a fresh directory opens", err == nil, fmt.Sprint(err))
	if store == nil {
		return finish(c)
	}
	stats := store.Stats()
	c.equal("a fresh log has one segment", stats.Segments, 1)
	c.equal("a fresh log has no records", stats.Records, 0)
	c.equal("a fresh log has no keys", stats.Keys, 0)

	c.that("put returns nil", store.Put("one", []byte("first")) == nil, "put failed")
	value, ok := store.Get("one")
	c.that("get finds the key", ok, "get missed a key that was just written")
	c.same("get returns the bytes", value, []byte("first"))
	c.equal("len counts the key", store.Len(), 1)

	value[0] = 'X'
	again, _ := store.Get("one")
	c.same("get returns a copy", again, []byte("first"))

	c.that("a second key lands", store.Put("two", []byte("second")) == nil, "put failed")
	keys := store.Keys()
	c.equal("keys are sorted", strings.Join(keys, ","), "one,two")

	removed, err := store.Delete("one")
	c.that("delete reports the removal", removed && err == nil, fmt.Sprint(removed, err))
	_, ok = store.Get("one")
	c.that("a deleted key is gone", !ok, "get found a deleted key")
	removed, _ = store.Delete("missing")
	c.that("deleting a missing key is a no-op", !removed, "delete claimed a missing key")

	c.equal("close does not fail", store.Close() == nil, true)

	// -- restart ----------------------------------------------------------
	reopened, err := Open(dir)
	c.that("the directory reopens", err == nil, fmt.Sprint(err))
	value, ok = reopened.Get("two")
	c.that("the surviving key is still there", ok, "replay lost a key")
	c.same("the surviving value is intact", value, []byte("second"))
	_, ok = reopened.Get("one")
	c.that("the tombstone survives the replay", !ok, "replay resurrected a deleted key")
	c.equal("the replay counts every record", reopened.Stats().Records, 3)

	// -- a torn tail ------------------------------------------------------
	handled := filepath.Join(mustTempDir(c), "torn")
	torn, err := Open(handled)
	c.that("the torn-tail store opens", err == nil, fmt.Sprint(err))
	torn.Put("kept", []byte("value"))
	segment := segmentPath(handled, 1)
	file, err := os.OpenFile(segment, os.O_APPEND|os.O_WRONLY, 0o644)
	c.that("the segment opens for the tail", err == nil, fmt.Sprint(err))
	file.Write([]byte{0x00, 0x00, 0x00, 0x40, 0x01, 0x02})
	file.Close()
	torn.Close()

	truncated, err := Open(handled)
	c.that("a torn tail still opens", err == nil, fmt.Sprint(err))
	recovery := truncated.Recovery()
	c.that("the torn tail is reported", recovery.TornTail, "recovery did not flag the tail")
	c.that("the dropped bytes are counted", recovery.DiscardedBytes > 0,
		fmt.Sprintf("discarded %d bytes", recovery.DiscardedBytes))
	value, ok = truncated.Get("kept")
	c.that("the record before the tail survives", ok, "the torn tail ate the good record")
	c.same("and its value is intact", value, []byte("value"))
	info, err := os.Stat(segment)
	c.that("the segment is truncated on disk", err == nil && info.Size() == int64(len(mustFrame(c, OpPut, "kept", []byte("value")))),
		fmt.Sprintf("size %d", mustSizeOrZero(segment)))

	// -- compaction -------------------------------------------------------
	packed := filepath.Join(mustTempDir(c), "packed")
	dense, err := Open(packed)
	c.that("the compaction store opens", err == nil, fmt.Sprint(err))
	for index := 0; index < 20; index++ {
		dense.Put(fmt.Sprintf("k%02d", index), []byte(strings.Repeat("v", 40)))
	}
	for index := 0; index < 5; index++ {
		dense.Delete(fmt.Sprintf("k%02d", index))
	}
	before := dense.Stats().Records
	written, after, err := dense.Compact()
	c.that("compaction succeeds", err == nil, fmt.Sprint(err))
	c.that("the record count shrinks", written == before && after == 15,
		fmt.Sprintf("before %d after %d", written, after))
	c.equal("the compacted log holds the live keys", dense.Stats().Keys, 15)
	c.equal("the compacted log is one segment", dense.Stats().Segments, 1)
	entries, err := os.ReadDir(packed)
	c.that("the directory lists", err == nil, fmt.Sprint(err))
	temporaries := 0
	for _, entry := range entries {
		if strings.HasSuffix(entry.Name(), ".tmp") {
			temporaries++
		}
	}
	c.equal("no temporary segment is left behind", temporaries, 0)
	_, ok = dense.Get("k00")
	c.that("a deleted key stays gone after compaction", !ok, "compaction resurrected a deleted key")
	survivor, ok := dense.Get("k19")
	c.that("a live key survives compaction", ok, "compaction dropped a live key")
	c.equal("and keeps its length", len(survivor), 40)
	dense.Close()

	reloaded, err := Open(packed)
	c.that("the compacted directory reopens", err == nil, fmt.Sprint(err))
	c.equal("the replay sees only live keys", reloaded.Len(), 15)
	reloaded.Close()

	// -- HTTP -------------------------------------------------------------
	apiDir := filepath.Join(mustTempDir(c), "api")
	live, err := Open(apiDir)
	c.that("the api store opens", err == nil, fmt.Sprint(err))
	server, port, err := Listen(live, "127.0.0.1:0")
	c.that("the server binds an ephemeral port", err == nil && port > 0, fmt.Sprint(err))
	go server.Serve()
	waitForServer(c, port)
	base := fmt.Sprintf("http://127.0.0.1:%d", port)
	client := &http.Client{Timeout: 5 * time.Second}

	status, body := request(c, client, http.MethodGet, base+"/health", nil)
	c.equal("health answers 200", status, 200)
	c.that("health names the key count", strings.Contains(body, `"keys":0`), body)

	status, body = request(c, client, http.MethodPut, base+"/kv/greeting", []byte("hello"))
	c.equal("put answers 201", status, 201)
	c.that("put echoes the key", strings.Contains(body, `"key":"greeting"`), body)

	status, body = request(c, client, http.MethodGet, base+"/kv/greeting", nil)
	c.equal("get answers 200", status, 200)
	c.equal("get returns the value", body, "hello")

	status, body = request(c, client, http.MethodGet, base+"/kv/absent", nil)
	c.equal("a missing key answers 404", status, 404)
	c.that("the 404 names the key", strings.Contains(body, `"key":"absent"`), body)

	status, _ = request(c, client, http.MethodPatch, base+"/kv/greeting", nil)
	c.equal("an unsupported method answers 405", status, 405)

	status, body = request(c, client, http.MethodGet, base+"/nope", nil)
	c.equal("an unknown route answers 404", status, 404)
	c.that("the unknown route names both parts", strings.Contains(body, "no route for GET /nope"), body)

	big := bytes.Repeat([]byte("x"), 70<<10)
	status, body = request(c, client, http.MethodPut, base+"/kv/big", big)
	c.equal("an oversized value answers 413", status, 413)
	c.that("the 413 explains itself", strings.Contains(body, "value_too_large"), body)

	status, body = request(c, client, http.MethodGet, base+"/wal", nil)
	c.equal("the wal endpoint answers 200", status, 200)
	c.that("the wal body counts records", strings.Contains(body, `"records":1`), body)

	status, body = request(c, client, http.MethodPost, base+"/compact", nil)
	c.equal("compaction over http answers 200", status, 200)
	c.that("compaction reports the shrink", strings.Contains(body, `"after":1`), body)

	status, _ = request(c, client, http.MethodDelete, base+"/kv/greeting", nil)
	c.equal("delete answers 204", status, 204)
	status, _ = request(c, client, http.MethodDelete, base+"/kv/greeting", nil)
	c.equal("deleting twice answers 404", status, 404)

	long := strings.Repeat("k", maxKeyLength+1)
	status, _ = request(c, client, http.MethodPut, base+"/kv/"+long, []byte("x"))
	c.equal("an over-long key answers 400", status, 400)

	context, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	c.that("shutdown succeeds", server.Shutdown(context) == nil, "shutdown failed")
	cancel()
	live.Close()

	persisted, err := Open(apiDir)
	c.that("the api directory reopens", err == nil, fmt.Sprint(err))
	c.equal("the deleted key is not replayed", persisted.Len(), 0)
	persisted.Close()

	return finish(c)
}

func finish(c *checker) int {
	if c.failed > 0 {
		fmt.Printf("selftest: %d checks, %d failed\n", c.checks, c.failed)
		return 1
	}
	fmt.Printf("selftest: %d checks, 0 failed\n", c.checks)
	return 0
}

func mustTempDir(c *checker) string {
	dir, err := os.MkdirTemp("", "walcache-")
	c.that("a temp directory is available", err == nil, fmt.Sprint(err))
	return dir
}

func mustFrame(c *checker, op byte, key string, value []byte) []byte {
	frame, err := encodeRecord(op, key, value)
	c.that("the reference frame encodes", err == nil, fmt.Sprint(err))
	return frame
}

func mustSizeOrZero(path string) int64 {
	info, err := os.Stat(path)
	if err != nil {
		return 0
	}
	return info.Size()
}

func waitForServer(c *checker, port int) {
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		connection, err := http.Get(fmt.Sprintf("http://127.0.0.1:%d/health", port))
		if err == nil {
			io.Copy(io.Discard, connection.Body)
			connection.Body.Close()
			c.that("the server answers", true, "")
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	c.that("the server answers", false, "the listener never came up")
}

func request(c *checker, client *http.Client, method, url string, payload []byte) (int, string) {
	var reader io.Reader
	if payload != nil {
		reader = bytes.NewReader(payload)
	}
	req, err := http.NewRequest(method, url, reader)
	if err != nil {
		c.that("the request builds", false, fmt.Sprint(err))
		return 0, ""
	}
	response, err := client.Do(req)
	if err != nil {
		c.that("the request reaches the server", false, fmt.Sprint(err))
		return 0, ""
	}
	defer response.Body.Close()
	body, _ := io.ReadAll(response.Body)
	return response.StatusCode, string(body)
}
