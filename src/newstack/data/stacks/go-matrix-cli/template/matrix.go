package main

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
)

// Matrix is a dense row-major matrix of float64 values.
type Matrix struct {
	Rows int
	Cols int
	Data [][]float64
}

// ParseMatrix decodes a JSON array of equally long numeric rows.
func ParseMatrix(text string) (Matrix, error) {
	var rows [][]float64
	if err := json.Unmarshal([]byte(text), &rows); err != nil {
		return Matrix{}, fmt.Errorf("matrix must be a JSON array of arrays: %v", err)
	}
	if len(rows) == 0 {
		return Matrix{}, fmt.Errorf("matrix has no rows")
	}
	cols := len(rows[0])
	if cols == 0 {
		return Matrix{}, fmt.Errorf("matrix rows must not be empty")
	}
	for index, row := range rows {
		if len(row) != cols {
			return Matrix{}, fmt.Errorf("row %d has %d value(s), expected %d", index+1, len(row), cols)
		}
	}
	return Matrix{Rows: len(rows), Cols: cols, Data: rows}, nil
}

// Identity returns the n×n identity matrix.
func Identity(n int) (Matrix, error) {
	if n <= 0 {
		return Matrix{}, fmt.Errorf("size must be positive, got %d", n)
	}
	data := make([][]float64, n)
	for i := range data {
		data[i] = make([]float64, n)
		data[i][i] = 1
	}
	return Matrix{Rows: n, Cols: n, Data: data}, nil
}

// Transpose swaps rows and columns.
func (m Matrix) Transpose() Matrix {
	data := make([][]float64, m.Cols)
	for j := 0; j < m.Cols; j++ {
		data[j] = make([]float64, m.Rows)
		for i := 0; i < m.Rows; i++ {
			data[j][i] = m.Data[i][j]
		}
	}
	return Matrix{Rows: m.Cols, Cols: m.Rows, Data: data}
}

// Multiply returns the matrix product, refusing incompatible shapes.
func Multiply(left, right Matrix) (Matrix, error) {
	if left.Cols != right.Rows {
		return Matrix{}, fmt.Errorf(
			"cannot multiply %dx%d by %dx%d: left columns must equal right rows",
			left.Rows, left.Cols, right.Rows, right.Cols)
	}
	data := make([][]float64, left.Rows)
	for i := 0; i < left.Rows; i++ {
		data[i] = make([]float64, right.Cols)
		for j := 0; j < right.Cols; j++ {
			var sum float64
			for k := 0; k < left.Cols; k++ {
				sum += left.Data[i][k] * right.Data[k][j]
			}
			data[i][j] = round(sum)
		}
	}
	return Matrix{Rows: left.Rows, Cols: right.Cols, Data: data}, nil
}

// round trims floating point noise so 0.30000000000000004 prints as 0.3.
func round(value float64) float64 {
	if math.Abs(value-math.Round(value)) < 1e-9 {
		return math.Round(value)
	}
	return math.Round(value*1e12) / 1e12
}

// Determinant uses Gaussian elimination with partial pivoting.
func (m Matrix) Determinant() (float64, error) {
	if m.Rows != m.Cols {
		return 0, fmt.Errorf("determinant needs a square matrix, got %dx%d", m.Rows, m.Cols)
	}
	n := m.Rows
	work := make([][]float64, n)
	for i := range work {
		work[i] = append([]float64(nil), m.Data[i]...)
	}
	det := 1.0
	for column := 0; column < n; column++ {
		pivot := column
		for row := column + 1; row < n; row++ {
			if math.Abs(work[row][column]) > math.Abs(work[pivot][column]) {
				pivot = row
			}
		}
		if math.Abs(work[pivot][column]) < 1e-12 {
			return 0, nil
		}
		if pivot != column {
			work[pivot], work[column] = work[column], work[pivot]
			det = -det
		}
		det *= work[column][column]
		for row := column + 1; row < n; row++ {
			factor := work[row][column] / work[column][column]
			for k := column; k < n; k++ {
				work[row][k] -= factor * work[column][k]
			}
		}
	}
	return round(det), nil
}

// Trace sums the main diagonal.
func (m Matrix) Trace() (float64, error) {
	if m.Rows != m.Cols {
		return 0, fmt.Errorf("trace needs a square matrix, got %dx%d", m.Rows, m.Cols)
	}
	var sum float64
	for i := 0; i < m.Rows; i++ {
		sum += m.Data[i][i]
	}
	return round(sum), nil
}

// String renders the matrix as JSON so the output stays machine readable.
func (m Matrix) String() string {
	encoded, err := json.Marshal(m.Data)
	if err != nil {
		return "[]"
	}
	return string(encoded)
}

// Describe adds the shape to a matrix rendering, e.g. "2x2 [[1,0],[0,1]]".
func (m Matrix) Describe() string {
	return fmt.Sprintf("%dx%d %s", m.Rows, m.Cols, m.String())
}

// FormatNumber prints a float without a trailing ".0" for whole values.
func FormatNumber(value float64) string {
	if value == math.Trunc(value) && math.Abs(value) < 1e15 {
		return fmt.Sprintf("%.0f", value)
	}
	return strings.TrimRight(strings.TrimRight(fmt.Sprintf("%.6f", value), "0"), ".")
}
