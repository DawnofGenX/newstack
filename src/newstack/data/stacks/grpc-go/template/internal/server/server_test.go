package server_test

import (
	"context"
	"net"
	"strings"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"

	textstatv1 "{{ npm_name }}/gen/textstat/v1"
	"{{ npm_name }}/internal/server"
)

// bufconn is an in-memory listener: it exercises the full gRPC stack (marshal, interceptors,
// status codes) without a socket, which is what keeps this test fast and flake-free.
func TestCountOverBufconn(t *testing.T) {
	listener := bufconn.Listen(1024 * 1024)
	grpcServer := grpc.NewServer()
	textstatv1.RegisterTextStatServiceServer(grpcServer, server.New())
	go func() {
		if err := grpcServer.Serve(listener); err != nil {
			t.Errorf("serve: %v", err)
		}
	}()
	t.Cleanup(grpcServer.Stop)

	conn, err := grpc.NewClient(
		"passthrough:///bufnet",
		grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) {
			return listener.Dial()
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	client := textstatv1.NewTextStatServiceClient(conn)
	response, err := client.Count(context.Background(), &textstatv1.CountRequest{Text: "hello world\n"})
	if err != nil {
		t.Fatalf("Count: %v", err)
	}
	if response.GetLines() != 1 || response.GetWords() != 2 || response.GetBytes() != 12 {
		t.Fatalf("counts = %+v, want lines=1 words=2 bytes=12", response)
	}
	if response.GetText() != "hello world\n" {
		t.Fatalf("echoed text = %q", response.GetText())
	}
}

// Invalid UTF-8 never reaches the handler: protobuf marshalling rejects it on the client.
// Asserting the real behaviour keeps the next reader from chasing a client-side error.
func TestInvalidUTF8IsRejectedByTheMarshaller(t *testing.T) {
	listener := bufconn.Listen(1024 * 1024)
	grpcServer := grpc.NewServer()
	textstatv1.RegisterTextStatServiceServer(grpcServer, server.New())
	go func() { _ = grpcServer.Serve(listener) }()
	t.Cleanup(grpcServer.Stop)

	conn, err := grpc.NewClient(
		"passthrough:///bufnet",
		grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) {
			return listener.Dial()
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	_, err = textstatv1.NewTextStatServiceClient(conn).Count(
		context.Background(),
		&textstatv1.CountRequest{Text: "\xff\xfe"},
	)
	if status.Code(err) != codes.Internal {
		t.Fatalf("code = %v, want Internal (err = %v)", status.Code(err), err)
	}
	if !strings.Contains(err.Error(), "invalid UTF-8") {
		t.Fatalf("err = %v, want it to mention invalid UTF-8", err)
	}
}

// The handler keeps its own guard, which matters for in-process callers (and for messages
// that arrive already unmarshalled).
func TestCountRejectsInvalidUTF8(t *testing.T) {
	response, err := server.New().Count(context.Background(), &textstatv1.CountRequest{Text: "\xff\xfe"})
	if response != nil {
		t.Fatalf("response = %v, want nil", response)
	}
	if status.Code(err) != codes.InvalidArgument {
		t.Fatalf("code = %v, want InvalidArgument (err = %v)", status.Code(err), err)
	}
	if !strings.Contains(err.Error(), "valid UTF-8") {
		t.Fatalf("err = %v, want it to mention valid UTF-8", err)
	}
}
