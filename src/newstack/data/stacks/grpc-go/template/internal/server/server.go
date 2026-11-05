// Package server implements the generated TextStat service. The generated interface is the
// only thing tying this file to gRPC, so the count rules stay in internal/textstat.
package server

import (
	"context"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	textstatv1 "{{ npm_name }}/gen/textstat/v1"
	"{{ npm_name }}/internal/textstat"
)

// Server implements textstatv1.TextStatServiceServer.
type Server struct {
	textstatv1.UnimplementedTextStatServiceServer
}

// New returns a Server with no state; every call is a pure function of its request.
func New() *Server { return &Server{} }

// Count measures the request's text. Invalid UTF-8 is an InvalidArgument rather than a 500:
// protobuf strings are bytes on the wire, so this is a caller mistake, not a server bug.
func (s *Server) Count(_ context.Context, req *textstatv1.CountRequest) (*textstatv1.CountResponse, error) {
	text := req.GetText()
	if !textstat.ValidUTF8(text) {
		return nil, status.Error(codes.InvalidArgument, "text must be valid UTF-8")
	}
	counts := textstat.Count(text)
	return &textstatv1.CountResponse{
		Text:  text,
		Lines: counts.Lines,
		Words: counts.Words,
		Bytes: counts.Bytes,
	}, nil
}
