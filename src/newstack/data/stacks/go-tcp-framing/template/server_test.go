package main

import (
	"context"
	"encoding/binary"
	"testing"
	"time"
)

func TestServerAnswersOverARealSocket(t *testing.T) {
	server, err := Listen("127.0.0.1:0", time.Second)
	if err != nil {
		t.Fatal(err)
	}
	go func() { _ = server.Serve() }()
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
	}()

	connection, err := dial(server.Addr())
	if err != nil {
		t.Fatal(err)
	}
	defer connection.close()

	reply, err := connection.send(`{"op":"count","text":"a b\nc\n"}`)
	if err != nil {
		t.Fatal(err)
	}
	if !reply.OK || *reply.Lines != 2 || *reply.Words != 3 || *reply.Bytes != 6 {
		t.Fatalf("got %+v", reply)
	}
}

func TestServerRefusesAnOversizedFrameAndKeepsServing(t *testing.T) {
	server, err := Listen("127.0.0.1:0", time.Second)
	if err != nil {
		t.Fatal(err)
	}
	go func() { _ = server.Serve() }()
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
	}()

	// Shutdown is asynchronous, so the goroutine above may not have entered
	// Accept yet; a retry loop makes the dial deterministic.
	bad := dialWithRetry(t, server.Addr())
	head := make([]byte, 4)
	binary.BigEndian.PutUint32(head, MaxFrame+1)
	if _, err := bad.conn.Write(head); err != nil {
		t.Fatal(err)
	}
	reply, err := bad.receive()
	if err != nil {
		t.Fatal(err)
	}
	if reply.Error != "frame_too_large" {
		t.Fatalf("got %+v", reply)
	}
	bad.close()

	good, err := dial(server.Addr())
	if err != nil {
		t.Fatal(err)
	}
	defer good.close()
	if reply, err := good.send(`{"op":"ping"}`); err != nil || !reply.OK {
		t.Fatalf("the listener stopped serving: %v %+v", err, reply)
	}
}

func dialWithRetry(t *testing.T, addr string) *client {
	t.Helper()
	var lastErr error
	for attempt := 0; attempt < 50; attempt++ {
		connection, err := dial(addr)
		if err == nil {
			return connection
		}
		lastErr = err
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatalf("cannot connect to %s: %v", addr, lastErr)
	return nil
}
