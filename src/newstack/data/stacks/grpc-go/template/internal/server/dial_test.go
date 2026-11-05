package server_test

import (
	"context"
	"net"
	"strconv"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	textstatv1 "{{ npm_name }}/gen/textstat/v1"
	"{{ npm_name }}/internal/server"
)

// bufconn proves the handler; this proves the socket. Port 0 lets the kernel pick a free
// one, so the test cannot collide with anything else on the machine.
func TestCountOverRealTCP(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	textstatv1.RegisterTextStatServiceServer(grpcServer, server.New())
	go func() {
		if err := grpcServer.Serve(listener); err != nil {
			t.Errorf("serve: %v", err)
		}
	}()
	t.Cleanup(grpcServer.Stop)

	address := net.JoinHostPort("127.0.0.1", strconv.Itoa(listener.Addr().(*net.TCPAddr).Port))
	conn, err := grpc.NewClient(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	response, err := textstatv1.NewTextStatServiceClient(conn).Count(
		context.Background(),
		&textstatv1.CountRequest{Text: "a b\nc\n"},
	)
	if err != nil {
		t.Fatalf("Count over TCP: %v", err)
	}
	if response.GetLines() != 2 || response.GetWords() != 3 || response.GetBytes() != 6 {
		t.Fatalf("counts = %+v, want lines=2 words=3 bytes=6", response)
	}
}
