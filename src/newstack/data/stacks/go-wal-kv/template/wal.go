package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"hash/crc32"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Op is the first byte of every log record.
const (
	OpPut    byte = 1
	OpDelete byte = 2
)

const (
	maxKeyLength   = 256
	maxValueLength = 1 << 20
)

// ErrTorn marks a record whose header or payload stops early: the process died
// mid-append. The store truncates it away and keeps the records before it.
var ErrTorn = errors.New("torn record")

// ErrCorrupt marks a record whose checksum does not match its payload.
var ErrCorrupt = errors.New("corrupt record")

// Record is one durable mutation.
type Record struct {
	Op    byte
	Key   string
	Value []byte
}

func encodeRecord(op byte, key string, value []byte) ([]byte, error) {
	if len(key) == 0 || len(key) > maxKeyLength {
		return nil, fmt.Errorf("key length %d is outside 1..%d", len(key), maxKeyLength)
	}
	if len(value) > maxValueLength {
		return nil, fmt.Errorf("value length %d is over %d", len(value), maxValueLength)
	}
	payload := make([]byte, 1+4+len(key)+4+len(value))
	payload[0] = op
	binary.BigEndian.PutUint32(payload[1:5], uint32(len(key)))
	copy(payload[5:], key)
	offset := 5 + len(key)
	binary.BigEndian.PutUint32(payload[offset:offset+4], uint32(len(value)))
	copy(payload[offset+4:], value)

	frame := make([]byte, 8+len(payload))
	binary.BigEndian.PutUint32(frame[0:4], uint32(len(payload)))
	binary.BigEndian.PutUint32(frame[4:8], crc32.ChecksumIEEE(payload))
	copy(frame[8:], payload)
	return frame, nil
}

// readRecord consumes one framed record. It returns the record and the number
// of bytes it used, so a caller that hits a bad tail knows where to truncate.
func readRecord(r io.Reader) (Record, int64, error) {
	header := make([]byte, 8)
	read, err := io.ReadFull(r, header)
	if err != nil {
		if errors.Is(err, io.EOF) && read == 0 {
			return Record{}, 0, io.EOF
		}
		return Record{}, 0, ErrTorn
	}
	length := binary.BigEndian.Uint32(header[0:4])
	want := binary.BigEndian.Uint32(header[4:8])
	if length < 9 || length > 1+4+maxKeyLength+4+maxValueLength {
		return Record{}, 0, ErrCorrupt
	}
	payload := make([]byte, length)
	if _, err := io.ReadFull(r, payload); err != nil {
		return Record{}, 0, ErrTorn
	}
	if crc32.ChecksumIEEE(payload) != want {
		return Record{}, 0, ErrCorrupt
	}
	op := payload[0]
	keyLength := binary.BigEndian.Uint32(payload[1:5])
	if keyLength == 0 || keyLength > maxKeyLength {
		return Record{}, 0, ErrCorrupt
	}
	if int(5+keyLength)+4 > len(payload) {
		return Record{}, 0, ErrCorrupt
	}
	key := string(payload[5 : 5+keyLength])
	valueLength := binary.BigEndian.Uint32(payload[5+keyLength : 9+keyLength])
	if int(9+keyLength)+int(valueLength) != len(payload) {
		return Record{}, 0, ErrCorrupt
	}
	value := append([]byte(nil), payload[9+keyLength:]...)
	return Record{Op: op, Key: key, Value: value}, int64(8 + length), nil
}

func segmentName(index int) string {
	return fmt.Sprintf("wal-%06d.log", index)
}

func segmentPath(dir string, index int) string {
	return filepath.Join(dir, segmentName(index))
}

// segmentIndexes lists the log files in a directory, oldest first. Temporary
// files from an interrupted compaction are ignored: only a rename makes a
// segment real.
func segmentIndexes(dir string) ([]int, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var out []int
	for _, entry := range entries {
		name := entry.Name()
		if entry.IsDir() || !strings.HasPrefix(name, "wal-") || !strings.HasSuffix(name, ".log") {
			continue
		}
		var index int
		if _, err := fmt.Sscanf(name, "wal-%06d.log", &index); err != nil || index <= 0 {
			continue
		}
		out = append(out, index)
	}
	sort.Ints(out)
	return out, nil
}

// Log appends records to one segment file.
type Log struct {
	dir     string
	file    *os.File
	segment int
	size    int64
}

func createSegment(dir string, index int) (*Log, error) {
	path := segmentPath(dir, index)
	file, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	return &Log{dir: dir, file: file, segment: index}, nil
}

func openSegment(dir string, index int) (*Log, error) {
	file, err := os.OpenFile(segmentPath(dir, index), os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return nil, err
	}
	info, err := file.Stat()
	if err != nil {
		file.Close()
		return nil, err
	}
	return &Log{dir: dir, file: file, segment: index, size: info.Size()}, nil
}

// Append writes one record and fsyncs it before returning: a Put that returns
// nil is on disk, which is the whole point of the log.
func (l *Log) Append(op byte, key string, value []byte) (int64, error) {
	frame, err := encodeRecord(op, key, value)
	if err != nil {
		return 0, err
	}
	if _, err := l.file.Write(frame); err != nil {
		return 0, err
	}
	if err := l.file.Sync(); err != nil {
		return 0, err
	}
	l.size += int64(len(frame))
	return int64(len(frame)), nil
}

func (l *Log) Close() error {
	if l == nil || l.file == nil {
		return nil
	}
	err := l.file.Close()
	l.file = nil
	return err
}

func (l *Log) Segment() int { return l.segment }

func (l *Log) Size() int64 { return l.size }
