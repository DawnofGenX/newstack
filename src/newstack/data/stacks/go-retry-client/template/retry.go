package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"time"
)

// Retryer performs HTTP requests with capped exponential backoff + jitter.
type Retryer struct {
	MaxAttempts int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
	Client      *http.Client
	// Sleep is invoked between attempts; defaults to time.Sleep.
	Sleep func(time.Duration)
	// Jitter returns an additional delay; defaults to random in [0, delay).
	Jitter func(time.Duration) time.Duration
}

func (r *Retryer) sleep(d time.Duration) {
	if r.Sleep != nil {
		r.Sleep(d)
		return
	}
	time.Sleep(d)
}

func (r *Retryer) jitter(d time.Duration) time.Duration {
	if r.Jitter != nil {
		return r.Jitter(d)
	}
	if d <= 0 {
		return 0
	}
	return time.Duration(rand.Int63n(int64(d)))
}

func (r *Retryer) maxAttempts() int {
	if r.MaxAttempts <= 0 {
		return 3
	}
	return r.MaxAttempts
}

func (r *Retryer) client() *http.Client {
	if r.Client != nil {
		return r.Client
	}
	return http.DefaultClient
}

// Do executes req, retrying on 5xx/429/network errors up to MaxAttempts.
func (r *Retryer) Do(req *http.Request) (*http.Response, error) {
	attempts := r.maxAttempts()
	var lastResp *http.Response
	var lastErr error
	for attempt := 0; attempt < attempts; attempt++ {
		// clone request for retry safety
		rq := req.Clone(req.Context())
		if req.GetBody != nil {
			b, _ := req.GetBody()
			rq.Body = b
		}
		resp, err := r.client().Do(rq)
		if err != nil {
			lastErr = err
			lastResp = nil
			if attempt == attempts-1 {
				return nil, err
			}
			r.sleep(r.delay(attempt))
			continue
		}
		lastResp = resp
		lastErr = nil
		// success or non-retryable
		if resp.StatusCode < 500 && resp.StatusCode != 429 {
			return resp, nil
		}
		// retryable status
		if attempt == attempts-1 {
			return resp, nil
		}
		resp.Body.Close()
		r.sleep(r.delay(attempt))
	}
	if lastErr != nil {
		return nil, lastErr
	}
	return lastResp, nil
}

func (r *Retryer) delay(attempt int) time.Duration {
	base := r.BaseDelay
	if base <= 0 {
		base = 100 * time.Millisecond
	}
	maxD := r.MaxDelay
	if maxD <= 0 {
		maxD = 5 * time.Second
	}
	d := base * (1 << attempt)
	if d > maxD {
		d = maxD
	}
	d += r.jitter(d / 2)
	if d > maxD {
		d = maxD
	}
	return d
}

func main() {
	// tiny CLI
	url := ""
	attempts := 3
	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-url" && i+1 < len(os.Args) {
			url = os.Args[i+1]
			i++
		} else if os.Args[i] == "-attempts" && i+1 < len(os.Args) {
			fmt.Sscan(os.Args[i+1], &attempts)
			i++
		}
	}
	if url == "" {
		fmt.Fprintln(os.Stderr, "usage: retryclient -url <url> [-attempts N]")
		os.Exit(2)
	}
	r := &Retryer{MaxAttempts: attempts, BaseDelay: 10 * time.Millisecond, MaxDelay: 50 * time.Millisecond}
	req, _ := http.NewRequest("GET", url, nil)
	resp, err := r.Do(req)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	fmt.Println(resp.StatusCode)
}