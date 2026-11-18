package main

import (
	"archive/tar"
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// ExtractArchive extracts a tar.gz stream from r into destDir safely.
func ExtractArchive(r io.Reader, destDir string) error {
	gz, err := gzip.NewReader(r)
	if err != nil {
		return fmt.Errorf("gzip: %w", err)
	}
	defer gz.Close()
	tr := tar.NewReader(gz)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("tar: %w", err)
		}
		if err := extractEntry(tr, hdr, destDir); err != nil {
			return err
		}
	}
	return nil
}

func extractEntry(tr *tar.Reader, hdr *tar.Header, destDir string) error {
	name := hdr.Name
	// reject absolute
	if filepath.IsAbs(name) {
		return fmt.Errorf("absolute path not allowed: %s", name)
	}
	clean := filepath.Clean(name)
	if clean == "." || clean == "" {
		return nil
	}
	if strings.HasPrefix(clean, "..") || strings.Contains(clean, string(filepath.Separator)+"..") {
		return fmt.Errorf("path traversal not allowed: %s", name)
	}
	// also check each component
	for _, part := range strings.Split(clean, string(filepath.Separator)) {
		if part == ".." {
			return fmt.Errorf("path traversal not allowed: %s", name)
		}
	}
	target := filepath.Join(destDir, clean)
	// ensure within dest
	rel, err := filepath.Rel(destDir, target)
	if err != nil || strings.HasPrefix(rel, "..") {
		return fmt.Errorf("path escapes destination: %s", name)
	}

	switch hdr.Typeflag {
	case tar.TypeDir:
		return os.MkdirAll(target, 0755)
	case tar.TypeReg:
		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			return err
		}
		f, err := os.OpenFile(target, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, os.FileMode(hdr.Mode))
		if err != nil {
			return err
		}
		defer f.Close()
		if _, err := io.Copy(f, tr); err != nil {
			return err
		}
		return nil
	case tar.TypeSymlink:
		return fmt.Errorf("symlinks not allowed: %s", name)
	default:
		return fmt.Errorf("unsupported entry type: %v", hdr.Typeflag)
	}
}

func main() {
	// minimal CLI
	if len(os.Args) < 4 {
		fmt.Fprintln(os.Stderr, "usage: tarextract -in archive.tar.gz -out dir")
		os.Exit(2)
	}
	var inPath, outDir string
	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-in" && i+1 < len(os.Args) {
			inPath = os.Args[i+1]
			i++
		} else if os.Args[i] == "-out" && i+1 < len(os.Args) {
			outDir = os.Args[i+1]
			i++
		}
	}
	f, err := os.Open(inPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer f.Close()
	if err := os.MkdirAll(outDir, 0755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := ExtractArchive(f, outDir); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}