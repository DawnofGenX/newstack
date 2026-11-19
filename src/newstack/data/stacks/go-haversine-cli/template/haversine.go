package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
)

const earthRadiusKm = 6371.0

// Haversine returns great-circle distance in kilometers.
func Haversine(lat1, lon1, lat2, lon2 float64) float64 {
	toRad := func(d float64) float64 { return d * math.Pi / 180.0 }
	dLat := toRad(lat2 - lat1)
	dLon := toRad(lon2 - lon1)
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(toRad(lat1))*math.Cos(toRad(lat2))*math.Sin(dLon/2)*math.Sin(dLon/2)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
	return earthRadiusKm * c
}

func main() {
	if len(os.Args) != 5 {
		fmt.Fprintln(os.Stderr, "usage: haversine <lat1> <lon1> <lat2> <lon2>")
		os.Exit(2)
	}
	parse := func(s string) float64 {
		v, err := strconv.ParseFloat(s, 64)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		return v
	}
	d := Haversine(parse(os.Args[1]), parse(os.Args[2]), parse(os.Args[3]), parse(os.Args[4]))
	fmt.Printf("%.3f\n", d)
}