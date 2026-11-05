// Command {{ npm_name }} serves the TextStat gRPC service.
package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	healthv1 "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"

	textstatv1 "{{ npm_name }}/gen/textstat/v1"
	"{{ npm_name }}/internal/server"
)

func main() {
	defaultAddress := "127.0.0.1:50051"
	if port := os.Getenv("PORT"); port != "" {
		defaultAddress = ":" + port
	}
	if addr := os.Getenv("ADDR"); addr != "" {
		defaultAddress = addr
	}
	address := flag.String("addr", defaultAddress, "listen address (host:port)")
	flag.Parse()

	listener, err := net.Listen("tcp", *address)
	if err != nil {
		log.Fatalf("listen %s: %v", *address, err)
	}

	grpcServer := grpc.NewServer()
	textstatv1.RegisterTextStatServiceServer(grpcServer, server.New())

	// The standard health service, so a load balancer or `grpc_health_probe` has something
	// standard to ask instead of a bespoke RPC.
	healthServer := health.NewServer()
	healthServer.SetServingStatus("textstat.v1.TextStatService", healthv1.HealthCheckResponse_SERVING)
	healthv1.RegisterHealthServer(grpcServer, healthServer)

	// Reflection is what lets grpcurl and any schema-discovering client work with no local
	// copies of the .proto files. It is cheap; production services usually keep it on.
	reflection.Register(grpcServer)

	fmt.Printf("listening on %s\n", listener.Addr())

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signals
		// Stop drains in-flight RPCs, which is the difference between a deploy and a burst
		// of client errors.
		stopped := make(chan struct{})
		go func() {
			grpcServer.GracefulStop()
			close(stopped)
		}()
		select {
		case <-stopped:
		case <-time.After(10 * time.Second):
			grpcServer.Stop()
		}
	}()

	if err := grpcServer.Serve(listener); err != nil && !errors.Is(err, grpc.ErrServerStopped) {
		log.Fatalf("serve: %v", err)
	}
}
