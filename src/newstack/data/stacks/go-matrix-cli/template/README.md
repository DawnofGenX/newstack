# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
echo '[[1,2],[3,4]]' | bin/app det          # det=-2
echo '[[1,2],[3,4]]' | bin/app trace        # trace=5
echo '[[1,2],[3,4]]' | bin/app transpose    # 2x2 [[1,3],[2,4]]
bin/app mul -file a.json -with b.json       # 2x2 [[2,1],[4,3]]
bin/app identity -size 3                    # 3x3 [[1,0,0],[0,1,0],[0,0,1]]
```

Matrices are JSON arrays of equally long numeric rows; a jagged matrix is
rejected with the offending row number. Determinants use Gaussian
elimination with partial pivoting, and results are rounded so
`0.1 + 0.2` prints as `0.3` instead of `0.30000000000000004`. Exit codes:
0 success, 1 bad input, 2 bad usage.
