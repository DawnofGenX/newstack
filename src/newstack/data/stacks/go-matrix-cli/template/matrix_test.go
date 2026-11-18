package main

import (
	"math"
	"testing"
)

func mustParse(t *testing.T, text string) Matrix {
	t.Helper()
	matrix, err := ParseMatrix(text)
	if err != nil {
		t.Fatalf("ParseMatrix(%q): %v", text, err)
	}
	return matrix
}

func TestParseMatrixReadsRows(t *testing.T) {
	matrix := mustParse(t, "[[1,2],[3,4]]")
	if matrix.Rows != 2 || matrix.Cols != 2 {
		t.Fatalf("shape = %dx%d, want 2x2", matrix.Rows, matrix.Cols)
	}
	if matrix.Data[1][0] != 3 {
		t.Fatalf("Data[1][0] = %v, want 3", matrix.Data[1][0])
	}
}

func TestParseMatrixRejectsJaggedInput(t *testing.T) {
	_, err := ParseMatrix("[[1,2],[3]]")
	if err == nil {
		t.Fatal("expected an error for a jagged matrix")
	}
	want := "row 2 has 1 value(s), expected 2"
	if err.Error() != want {
		t.Fatalf("error = %q, want %q", err.Error(), want)
	}
}

func TestParseMatrixRejectsEmptyInput(t *testing.T) {
	if _, err := ParseMatrix("[]"); err == nil {
		t.Fatal("expected an error for an empty matrix")
	}
	if _, err := ParseMatrix("[[],[]]"); err == nil {
		t.Fatal("expected an error for empty rows")
	}
}

func TestTransposeSwapsShape(t *testing.T) {
	got := mustParse(t, "[[1,2,3],[4,5,6]]").Transpose()
	if got.Describe() != "3x2 [[1,4],[2,5],[3,6]]" {
		t.Fatalf("transpose = %s", got.Describe())
	}
}

func TestMultiplyProducesTheProduct(t *testing.T) {
	product, err := Multiply(mustParse(t, "[[1,2],[3,4]]"), mustParse(t, "[[0,1],[1,0]]"))
	if err != nil {
		t.Fatalf("Multiply: %v", err)
	}
	if product.String() != "[[2,1],[4,3]]" {
		t.Fatalf("product = %s", product.String())
	}
}

func TestMultiplyRejectsIncompatibleShapes(t *testing.T) {
	_, err := Multiply(mustParse(t, "[[1,2]]"), mustParse(t, "[[1,2]]"))
	if err == nil {
		t.Fatal("expected a shape error")
	}
}

func TestDeterminant(t *testing.T) {
	cases := []struct {
		matrix string
		want   float64
	}{
		{"[[5]]", 5},
		{"[[1,2],[3,4]]", -2},
		{"[[6,1,1],[4,-2,5],[2,8,7]]", -306},
		{"[[1,0,0],[0,1,0],[0,0,1]]", 1},
		{"[[1,2],[2,4]]", 0},
	}
	for _, test := range cases {
		got, err := mustParse(t, test.matrix).Determinant()
		if err != nil {
			t.Fatalf("Determinant(%s): %v", test.matrix, err)
		}
		if got != test.want {
			t.Fatalf("Determinant(%s) = %v, want %v", test.matrix, got, test.want)
		}
	}
}

func TestDeterminantNeedsASquareMatrix(t *testing.T) {
	if _, err := mustParse(t, "[[1,2,3],[4,5,6]]").Determinant(); err == nil {
		t.Fatal("expected an error for a rectangular matrix")
	}
}

func TestTrace(t *testing.T) {
	got, err := mustParse(t, "[[1,2],[3,4]]").Trace()
	if err != nil || got != 5 {
		t.Fatalf("Trace = %v, %v", got, err)
	}
}

func TestIdentity(t *testing.T) {
	identity, err := Identity(3)
	if err != nil {
		t.Fatalf("Identity: %v", err)
	}
	if identity.String() != "[[1,0,0],[0,1,0],[0,0,1]]" {
		t.Fatalf("identity = %s", identity.String())
	}
	if _, err := Identity(0); err == nil {
		t.Fatal("expected an error for a zero size")
	}
}

func TestFormatNumberTrimsTrailingZeros(t *testing.T) {
	cases := map[float64]string{-2: "-2", 0.5: "0.5", 1.0 / 3.0: "0.333333"}
	for value, want := range cases {
		if got := FormatNumber(value); got != want {
			t.Fatalf("FormatNumber(%v) = %q, want %q", value, got, want)
		}
	}
	if math.Abs(round(0.1+0.2)-0.3) > 1e-12 {
		t.Fatal("round should remove floating point noise")
	}
}
