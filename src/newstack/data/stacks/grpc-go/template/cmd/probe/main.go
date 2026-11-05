// Command probe is a minimal gRPC client for the service: it dials, calls Count once, and
// prints the counts. It is what the CI smoke test uses to prove a real client can talk to a
// real server, and it doubles as documentation of the client side.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	textstatv1 "{{ npm_name }}/gen/textstat/v1"
)

func main() {
	address := flag.String("addr", "127.0.0.1:50051", "address of the TextStat service")
	text := flag.String("text", "hello world\n", "text to count (\\n escapes are honoured)")
	flag.Parse()

	// The shell hands us literal backslash sequences from a single-quoted argument, so the
	// flag means what a user typing `-text 'a b\nc\n'` expects: a real newline.
	counted := unescape(*text)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	conn, err := grpc.NewClient(*address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		fmt.Fprintf(os.Stderr, "dial %s: %v\n", *address, err)
		os.Exit(1)
	}
	defer func() { _ = conn.Close() }()

	response, err := textstatv1.NewTextStatServiceClient(conn).Count(ctx, &textstatv1.CountRequest{Text: counted})
	if err != nil {
		fmt.Fprintf(os.Stderr, "count: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("lines=%d words=%d bytes=%d\n", response.GetLines(), response.GetWords(), response.GetBytes())
}

// unescape turns the escape sequences a shell single-quoted argument carries literally
// (backslash-n, backslash-t, doubled backslash) into the bytes they stand for, so the flag
// means what the help text promises.
func unescape(text string) string {
	var out strings.Builder
	for i := 0; i < len(text); i++ {
		if text[i] != '\\' || i+1 == len(text) {
			out.WriteByte(text[i])
			continue
		}
		i++
		switch text[i] {
		case 'n':
			out.WriteByte('\n')
		case 't':
			out.WriteByte('\t')
		case '\\':
			out.WriteByte('\\')
		default:
			out.WriteByte('\\')
			out.WriteByte(text[i])
		}
	}
	return out.String()
}
