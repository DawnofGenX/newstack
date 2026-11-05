package main

import (
	"encoding/json"
	"errors"
)

// Reply is what a client always gets back: exactly one frame per request.
// The count fields are pointers so a zero is printed instead of omitted --
// "lines":0 is an answer, not a missing key.
type Reply struct {
	OK     bool   `json:"ok"`
	Pong   *bool  `json:"pong,omitempty"`
	Lines  *int   `json:"lines,omitempty"`
	Words  *int   `json:"words,omitempty"`
	Bytes  *int   `json:"bytes,omitempty"`
	Error  string `json:"error,omitempty"`
	Detail string `json:"detail,omitempty"`
}

type request struct {
	Op   *string `json:"op"`
	Text *string `json:"text"`
}

func ok() *bool {
	value := true
	return &value
}

func fail(kind, detail string) Reply {
	return Reply{OK: false, Error: kind, Detail: detail}
}

// Answer turns one request frame into one reply frame. It never returns an
// error: a protocol mistake is a reply, because a client that gets a frame
// back can keep using the connection.
func Answer(payload []byte) Reply {
	var request request
	if err := json.Unmarshal(payload, &request); err != nil {
		return fail("invalid_json", err.Error())
	}
	if request.Op == nil {
		return fail("missing_op", `the frame has no "op" member`)
	}
	switch *request.Op {
	case "ping":
		return Reply{OK: true, Pong: ok()}
	case "count":
		if request.Text == nil {
			return fail("missing_text", `the count op needs a "text" member`)
		}
		counts := CountText(*request.Text)
		return Reply{OK: true, Lines: &counts.Lines, Words: &counts.Words, Bytes: &counts.Bytes}
	default:
		return fail("unknown_op", "no op named "+*request.Op)
	}
}

// Encode marshals a reply; a marshal failure here is a programming error.
func Encode(reply Reply) ([]byte, error) {
	payload, err := json.Marshal(reply)
	if err != nil {
		return nil, errors.New("cannot encode reply: " + err.Error())
	}
	return payload, nil
}
