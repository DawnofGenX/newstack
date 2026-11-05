package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// State remembers which job ids finished, so a replayed file does not redo the
// work. It is written with a temp file plus rename: a worker that is killed
// mid-write leaves either the old file or the new one, never half of each.
type State struct {
	Version int               `json:"version"`
	Done    map[string]string `json:"done"`
	path    string
}

func loadState(path string) (*State, error) {
	state := &State{Version: 1, Done: map[string]string{}, path: path}
	raw, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return state, nil
		}
		return nil, err
	}
	if len(raw) == 0 {
		return state, nil
	}
	if err := json.Unmarshal(raw, state); err != nil {
		return nil, err
	}
	if state.Done == nil {
		state.Done = map[string]string{}
	}
	state.path = path
	return state, nil
}

// finished reports whether the job already succeeded. A failed job is recorded
// but not finished: a replay retries it, which is the whole point of a retry
// budget.
func (s *State) finished(id string) bool {
	return s.Done[id] == statusOK
}

func (s *State) record(id, status string) {
	s.Done[id] = status
}

func (s *State) save() error {
	raw, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	dir := filepath.Dir(s.path)
	if dir != "." && dir != "" {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	temp, err := os.CreateTemp(dir, ".seen-*.json")
	if err != nil {
		return err
	}
	name := temp.Name()
	if _, err := temp.Write(raw); err != nil {
		temp.Close()
		os.Remove(name)
		return err
	}
	if err := temp.Sync(); err != nil {
		temp.Close()
		os.Remove(name)
		return err
	}
	if err := temp.Close(); err != nil {
		os.Remove(name)
		return err
	}
	return os.Rename(name, s.path)
}
