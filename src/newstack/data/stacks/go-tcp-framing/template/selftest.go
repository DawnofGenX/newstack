package main

import (
	"bufio"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"net"
	"strings"
	"sync"
	"time"
)

type checker struct {
	checks   int
	failures int
}

func (c *checker) that(name string, ok bool, detail string) {
	c.checks++
	if ok {
		return
	}
	c.failures++
	if detail != "" {
		fmt.Printf("FAIL %s: %s\n", name, detail)
		return
	}
	fmt.Printf("FAIL %s\n", name)
}

func (c *checker) equal(name string, got, want any) {
	c.that(name, fmt.Sprint(got) == fmt.Sprint(want), fmt.Sprintf("got %v want %v", got, want))
}

// client is the test's view of one connection.
type client struct {
	conn net.Conn
	read *bufio.Reader
}

func dial(addr string) (*client, error) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return nil, err
	}
	_ = conn.SetDeadline(time.Now().Add(10 * time.Second))
	return &client{conn: conn, read: bufio.NewReader(conn)}, nil
}

func (c *client) send(payload string) (Reply, error) {
	if err := WriteFrame(c.conn, []byte(payload)); err != nil {
		return Reply{}, err
	}
	return c.receive()
}

func (c *client) receive() (Reply, error) {
	payload, err := ReadFrame(c.read, MaxFrame)
	if err != nil {
		return Reply{}, err
	}
	var reply Reply
	if err := json.Unmarshal(payload, &reply); err != nil {
		return Reply{}, err
	}
	return reply, nil
}

func (c *client) close() {
	_ = c.conn.Close()
}

// RunSelfTest starts a real listener on port 0 and talks to it over TCP: a
// fake in-memory transport would not prove that frames survive a socket.
func RunSelfTest() error {
	// A two-second idle deadline keeps the suite quick; the shipped default is 30s.
	server, err := Listen("127.0.0.1:0", 2*time.Second)
	if err != nil {
		return err
	}
	go func() { _ = server.Serve() }()
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
	}()

	c := &checker{}
	connection, err := dial(server.Addr())
	if err != nil {
		return err
	}
	defer connection.close()

	reply, err := connection.send(`{"op":"ping"}`)
	c.that("ping answers", err == nil && reply.OK && reply.Pong != nil && *reply.Pong, fmt.Sprint(err))

	reply, err = connection.send(`{"op":"count","text":"a b\nc\n"}`)
	c.that("count sub", err == nil && reply.OK, fmt.Sprint(err))
	if reply.OK {
		c.equal("count lines", *reply.Lines, 2)
		c.equal("count words", *reply.Words, 3)
		c.equal("count bytes", *reply.Bytes, 6)
	}

	reply, _ = connection.send(`{"op":"count","text":""}`)
	c.that("empty text is an answer, not an error", reply.OK, reply.Error)
	if reply.OK {
		c.equal("empty lines", *reply.Lines, 0)
		c.equal("empty words", *reply.Words, 0)
		c.equal("empty bytes", *reply.Bytes, 0)
	}

	reply, _ = connection.send(`{"op":"count","text":"h\u00e9llo w\u00f6rld\n"}`)
	c.that("utf8 counts bytes", reply.OK && *reply.Bytes == 14 && *reply.Words == 2 && *reply.Lines == 1,
		fmt.Sprintf("%+v", reply))

	reply, _ = connection.send(`{"op":"count"}`)
	c.equal("missing text is named", reply.Error, "missing_text")
	c.equal("missing text is not ok", reply.OK, false)

	reply, _ = connection.send(`{"op":"count","text":42}`)
	c.equal("a number is not text", reply.Error, "invalid_json")

	reply, _ = connection.send(`{"op":"nope"}`)
	c.equal("unknown op", reply.Error, "unknown_op")
	c.that("unknown op names itself", strings.Contains(reply.Detail, "nope"), reply.Detail)

	reply, _ = connection.send(`{"text":"a b"}`)
	c.equal("missing op", reply.Error, "missing_op")

	reply, _ = connection.send(`not json at all`)
	c.equal("broken json", reply.Error, "invalid_json")

	reply, _ = connection.send(`{"op":"count","text":"a\u0000b"}`)
	c.that("an embedded NUL is a byte", reply.OK && *reply.Bytes == 3 && *reply.Words == 1, fmt.Sprintf("%+v", reply))

	// The connection is still usable after seven errors.
	reply, err = connection.send(`{"op":"ping"}`)
	c.that("the connection survives protocol errors", err == nil && reply.OK, fmt.Sprint(err))

	big := strings.Repeat("x ", 4000)
	reply, err = connection.send(`{"op":"count","text":"` + big + `"}`)
	c.that("a 8 KB frame is ordinary traffic", err == nil && reply.OK && *reply.Bytes == 8000, fmt.Sprint(err))
	if reply.OK {
		c.equal("the 8 KB frame has 4000 words", *reply.Words, 4000)
	}

	// A frame header that promises more than MaxFrame must be refused before
	// the body is read.
	oversized, err := dial(server.Addr())
	if err == nil {
		head := make([]byte, 4)
		binary.BigEndian.PutUint32(head, MaxFrame+1)
		_, _ = oversized.conn.Write(head)
		reply, err = oversized.receive()
		c.that("an oversized frame is refused", err == nil && reply.Error == "frame_too_large", fmt.Sprint(err))
		oversized.close()
	} else {
		c.that("an oversized frame is refused", false, err.Error())
	}

	// A zero-length frame is a framing mistake, not an empty message.
	empty, err := dial(server.Addr())
	if err == nil {
		_, _ = empty.conn.Write([]byte{0, 0, 0, 0})
		reply, err = empty.receive()
		c.that("an empty frame is refused", err == nil && reply.Error == "empty_frame", fmt.Sprint(err))
		empty.close()
	}

	// Two connections, ten requests each, all in order.
	var wait sync.WaitGroup
	results := make([][]int, 2)
	for index := 0; index < 2; index++ {
		wait.Add(1)
		go func(slot int) {
			defer wait.Done()
			other, err := dial(server.Addr())
			if err != nil {
				return
			}
			defer other.close()
			for step := 1; step <= 10; step++ {
				reply, err := other.send(fmt.Sprintf(`{"op":"count","text":"%s"}`, strings.Repeat("a", step)))
				if err != nil || !reply.OK {
					return
				}
				results[slot] = append(results[slot], *reply.Bytes)
			}
		}(index)
	}
	wait.Wait()
	for slot := 0; slot < 2; slot++ {
		ordered := len(results[slot]) == 10
		for step := 0; ordered && step < 10; step++ {
			ordered = results[slot][step] == step+1
		}
		c.that(fmt.Sprintf("connection %d kept its order", slot), ordered, fmt.Sprint(results[slot]))
	}

	// Separator-only and CRLF payloads: a word needs a non-separator byte.
	reply, _ = connection.send(`{"op":"count","text":" \t \r\n"}`)
	c.that("separators alone are no words", reply.OK && *reply.Words == 0 && *reply.Lines == 1, fmt.Sprintf("%+v", reply))

	reply, _ = connection.send(`{"op":"count","text":"a\tb\u000bc\u000cd"}`)
	c.that("tab, vertical tab and form feed all break words", reply.OK && *reply.Words == 4, fmt.Sprintf("%+v", reply))

	// A member the protocol does not know is ignored, not an error: a client
	// that gains a field must not have to wait for the server to learn it.
	reply, _ = connection.send(`{"op":"count","text":"a b","extra":{"nested":true}}`)
	c.that("unknown members are ignored", reply.OK && *reply.Words == 2, fmt.Sprintf("%+v", reply))

	// Exactly MaxFrame is legal; one byte more is not.
	filler := MaxFrame - len(`{"op":"count","text":""}`)
	reply, err = connection.send(`{"op":"count","text":"` + strings.Repeat("a", filler) + `"}`)
	c.that("a frame of exactly MaxFrame is legal", err == nil && reply.OK, fmt.Sprint(err))
	if reply.OK {
		c.equal("the boundary frame counted every byte", *reply.Bytes, filler)
	}

	// A silent client is dropped by the idle deadline instead of leaking a
	// goroutine for the life of the process.
	silent, err := dial(server.Addr())
	if err == nil {
		_ = silent.conn.SetReadDeadline(time.Now().Add(6 * time.Second))
		started := time.Now()
		_, err = silent.receive()
		c.that("an idle connection is closed by the server", err != nil && time.Since(started) < 5*time.Second, fmt.Sprint(err))
		silent.close()
	}

	// Shutdown has to close a parked client, otherwise Ctrl-C hangs.
	parked, err := dial(server.Addr())
	if err == nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		done := make(chan error, 1)
		go func() { done <- server.Shutdown(ctx) }()
		_ = parked.conn.SetReadDeadline(time.Now().Add(5 * time.Second))
		_, err = parked.receive()
		shutdownErr := <-done
		cancel()
		c.that("shutdown closes a parked client", err != nil && shutdownErr == nil, fmt.Sprint(shutdownErr))
		parked.close()
	}

	if c.failures != 0 {
		return fmt.Errorf("%d of %d checks failed", c.failures, c.checks)
	}
	fmt.Printf("selftest: %d checks passed\n", c.checks)
	return nil
}
