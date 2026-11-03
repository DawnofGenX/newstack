package api

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

type call struct {
	label      string
	method     string
	target     string
	body       string
	wantStatus int
	check      func(t *testing.T, body []byte)
}

func decode[T any](t *testing.T, body []byte) T {
	t.Helper()
	var out T
	if err := json.Unmarshal(body, &out); err != nil {
		t.Fatalf("invalid JSON %q: %v", string(body), err)
	}
	return out
}

func TestHandler(t *testing.T) {
	tests := []struct {
		name  string
		calls []call
	}{
		{
			name: "health reports ok",
			calls: []call{{
				label:      "GET /health",
				method:     http.MethodGet,
				target:     "/health",
				wantStatus: http.StatusOK,
				check: func(t *testing.T, body []byte) {
					got := decode[map[string]string](t, body)
					if got["status"] != "ok" {
						t.Errorf("status = %q, want %q", got["status"], "ok")
					}
				},
			}},
		},
		{
			name: "items starts empty",
			calls: []call{{
				label:      "GET /items",
				method:     http.MethodGet,
				target:     "/items",
				wantStatus: http.StatusOK,
				check: func(t *testing.T, body []byte) {
					items := decode[[]Item](t, body)
					if len(items) != 0 {
						t.Errorf("items = %v, want empty", items)
					}
				},
			}},
		},
		{
			name: "post then get returns the item",
			calls: []call{
				{
					label:      "POST /items",
					method:     http.MethodPost,
					target:     "/items",
					body:       `{"name":"probe"}`,
					wantStatus: http.StatusCreated,
					check: func(t *testing.T, body []byte) {
						item := decode[Item](t, body)
						if item.Name != "probe" {
							t.Errorf("name = %q, want %q", item.Name, "probe")
						}
						if item.ID == 0 {
							t.Errorf("id = 0, want a non-zero id")
						}
					},
				},
				{
					label:      "GET /items after POST",
					method:     http.MethodGet,
					target:     "/items",
					wantStatus: http.StatusOK,
					check: func(t *testing.T, body []byte) {
						items := decode[[]Item](t, body)
						if len(items) != 1 {
							t.Fatalf("items = %v, want exactly one", items)
						}
						if items[0].Name != "probe" {
							t.Errorf("name = %q, want %q", items[0].Name, "probe")
						}
					},
				},
			},
		},
		{
			name: "post with invalid JSON is rejected",
			calls: []call{{
				label:      "POST /items invalid",
				method:     http.MethodPost,
				target:     "/items",
				body:       `{"name":`,
				wantStatus: http.StatusBadRequest,
				check: func(t *testing.T, body []byte) {
					got := decode[map[string]string](t, body)
					if got["error"] == "" {
						t.Errorf("body = %q, want an error message", string(body))
					}
				},
			}},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			srv := httptest.NewServer(Handler())
			defer srv.Close()

			for _, c := range tt.calls {
				var reader io.Reader
				if c.body != "" {
					reader = bytes.NewBufferString(c.body)
				}
				req, err := http.NewRequest(c.method, srv.URL+c.target, reader)
				if err != nil {
					t.Fatalf("%s: build request: %v", c.label, err)
				}
				if c.body != "" {
					req.Header.Set("Content-Type", "application/json")
				}

				resp, err := srv.Client().Do(req)
				if err != nil {
					t.Fatalf("%s: request failed: %v", c.label, err)
				}
				payload, err := io.ReadAll(resp.Body)
				resp.Body.Close()
				if err != nil {
					t.Fatalf("%s: read body: %v", c.label, err)
				}

				if resp.StatusCode != c.wantStatus {
					t.Fatalf("%s: status = %d, want %d (body: %s)",
						c.label, resp.StatusCode, c.wantStatus, payload)
				}
				if got := resp.Header.Get("Content-Type"); got != "application/json" {
					t.Errorf("%s: content-type = %q, want %q", c.label, got, "application/json")
				}
				if c.check != nil {
					c.check(t, payload)
				}
			}
		})
	}
}

func TestStoreIsConcurrencySafe(t *testing.T) {
	store := NewStore()
	done := make(chan struct{})

	for i := 0; i < 8; i++ {
		go func() {
			defer func() { done <- struct{}{} }()
			store.Create("x")
			store.List()
		}()
	}
	for i := 0; i < 8; i++ {
		<-done
	}

	if got := len(store.List()); got != 8 {
		t.Errorf("len(items) = %d, want 8", got)
	}
}
