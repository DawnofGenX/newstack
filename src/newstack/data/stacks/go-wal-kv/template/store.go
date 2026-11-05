package main

import (
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"sync"
)

// Recovery reports what the log replay found when the store was opened.
type Recovery struct {
	Segments       int   `json:"segments"`
	Records        int   `json:"records"`
	DiscardedBytes int64 `json:"discarded_bytes"`
	TornTail       bool  `json:"torn_tail"`
}

// Stats is the shape the /wal endpoint returns.
type Stats struct {
	Keys             int    `json:"keys"`
	Records          int    `json:"records"`
	Segments         int    `json:"segments"`
	Bytes            int64  `json:"bytes"`
	Compactions      int    `json:"compactions"`
	DiscardedBytes   int64  `json:"discarded_bytes"`
	SegmentIndexHint string `json:"segment"`
}

// Store keeps the live map in memory and every mutation in the log.
type Store struct {
	mu       sync.RWMutex
	dir      string
	data     map[string][]byte
	log      *Log
	records  int
	segments int
	recovery Recovery
	compacts int
}

// Open replays the directory and returns a store ready for use.
func Open(dir string) (*Store, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	indexes, err := segmentIndexes(dir)
	if err != nil {
		return nil, err
	}
	store := &Store{dir: dir, data: make(map[string][]byte)}
	store.recovery.Segments = len(indexes)

	if len(indexes) == 0 {
		log, err := createSegment(dir, 1)
		if err != nil {
			return nil, err
		}
		store.log = log
		store.segments = 1
		return store, nil
	}

	for position, index := range indexes {
		last := position == len(indexes)-1
		applied, _, discarded, torn, err := replaySegment(segmentPath(dir, index), store.data)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", segmentName(index), err)
		}
		store.records += applied
		store.recovery.Records += applied
		if torn {
			if !last {
				return nil, fmt.Errorf("%s: torn record in a sealed segment", segmentName(index))
			}
			store.recovery.TornTail = true
			store.recovery.DiscardedBytes = discarded
			if err := os.Truncate(segmentPath(dir, index), mustSize(segmentPath(dir, index))-discarded); err != nil {
				return nil, err
			}
		}
	}

	log, err := openSegment(dir, indexes[len(indexes)-1])
	if err != nil {
		return nil, err
	}
	store.log = log
	store.segments = len(indexes)
	return store, nil
}

func mustSize(path string) int64 {
	info, err := os.Stat(path)
	if err != nil {
		return 0
	}
	return info.Size()
}

// replaySegment applies one segment to the map and reports how much of the
// file was usable. A torn last record is the normal crash shape, so the caller
// truncates it; a bad checksum in the middle of a segment is a real error.
func replaySegment(path string, data map[string][]byte) (applied int, consumed, discarded int64, torn bool, err error) {
	file, err := os.Open(path)
	if err != nil {
		return 0, 0, 0, false, err
	}
	defer file.Close()

	total := mustSize(path)
	for {
		record, size, readErr := readRecord(file)
		if errors.Is(readErr, io.EOF) {
			return applied, consumed, 0, false, nil
		}
		if readErr != nil {
			if errors.Is(readErr, ErrTorn) {
				return applied, consumed, total - consumed, true, nil
			}
			return applied, consumed, 0, false, readErr
		}
		applyRecord(data, record)
		applied++
		consumed += size
	}
}

func applyRecord(data map[string][]byte, record Record) {
	switch record.Op {
	case OpPut:
		data[record.Key] = record.Value
	case OpDelete:
		delete(data, record.Key)
	}
}

// Dir is the log directory.
func (s *Store) Dir() string { return s.dir }

// Put appends the record first and only then mutates memory: a caller that
// gets nil can restart the process and still read the value back.
func (s *Store) Put(key string, value []byte) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	size, err := s.log.Append(OpPut, key, value)
	if err != nil {
		return err
	}
	s.data[key] = append([]byte(nil), value...)
	s.records++
	if err := s.account(size); err != nil {
		return err
	}
	return nil
}

// Delete writes a tombstone; the value stays in the log until a compaction.
func (s *Store) Delete(key string) (bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.data[key]; !ok {
		return false, nil
	}
	size, err := s.log.Append(OpDelete, key, nil)
	if err != nil {
		return false, err
	}
	delete(s.data, key)
	s.records++
	if err := s.account(size); err != nil {
		return false, err
	}
	return true, nil
}

func (s *Store) account(size int64) error {
	s.recovery.Records = s.records
	_ = size
	return nil
}

// Get returns a copy so a caller cannot mutate the store behind the lock.
func (s *Store) Get(key string) ([]byte, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	value, ok := s.data[key]
	if !ok {
		return nil, false
	}
	return append([]byte(nil), value...), true
}

// Len is the number of live keys.
func (s *Store) Len() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.data)
}

// Keys returns the live keys in sorted order.
func (s *Store) Keys() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	keys := make([]string, 0, len(s.data))
	for key := range s.data {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

// Compact rewrites the directory as one segment holding every live key.
// It returns the record count before and after, so a caller can see the work.
func (s *Store) Compact() (int, int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	before := s.records
	next := s.log.Segment() + 1
	temporary := segmentPath(s.dir, next) + ".tmp"

	file, err := os.OpenFile(temporary, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return before, before, err
	}
	snapshot := make([]string, 0, len(s.data))
	for key := range s.data {
		snapshot = append(snapshot, key)
	}
	sort.Strings(snapshot)
	written := 0
	for _, key := range snapshot {
		frame, err := encodeRecord(OpPut, key, s.data[key])
		if err != nil {
			file.Close()
			os.Remove(temporary)
			return before, before, err
		}
		if _, err := file.Write(frame); err != nil {
			file.Close()
			os.Remove(temporary)
			return before, before, err
		}
		written++
	}
	if err := file.Sync(); err != nil {
		file.Close()
		os.Remove(temporary)
		return before, before, err
	}
	if err := file.Close(); err != nil {
		os.Remove(temporary)
		return before, before, err
	}
	if err := os.Rename(temporary, segmentPath(s.dir, next)); err != nil {
		os.Remove(temporary)
		return before, before, err
	}

	if err := s.log.Close(); err != nil {
		return before, before, err
	}
	indexes, err := segmentIndexes(s.dir)
	if err != nil {
		return before, before, err
	}
	for _, index := range indexes {
		if index >= next {
			continue
		}
		if err := os.Remove(segmentPath(s.dir, index)); err != nil {
			return before, before, err
		}
	}
	log, err := openSegment(s.dir, next)
	if err != nil {
		return before, before, err
	}
	s.log = log
	s.segments = 1
	s.records = written
	s.recovery.Records = written
	s.recovery.Segments = 1
	s.recovery.DiscardedBytes = 0
	s.recovery.TornTail = false
	s.compacts++
	return before, written, nil
}

// Stats is a consistent snapshot for /wal and /health.
func (s *Store) Stats() Stats {
	s.mu.RLock()
	defer s.mu.RUnlock()
	size := int64(0)
	if indexes, err := segmentIndexes(s.dir); err == nil {
		for _, index := range indexes {
			size += mustSize(segmentPath(s.dir, index))
		}
	}
	return Stats{
		Keys:             len(s.data),
		Records:          s.records,
		Segments:         s.segments,
		Bytes:            size,
		Compactions:      s.compacts,
		DiscardedBytes:   s.recovery.DiscardedBytes,
		SegmentIndexHint: segmentName(s.log.Segment()),
	}
}

// Close flushes and releases the log file.
func (s *Store) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.log.Close()
}

// Recovery exposes what the replay found, for the selftest and the health body.
func (s *Store) Recovery() Recovery {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.recovery
}
