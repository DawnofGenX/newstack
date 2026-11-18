using Xunit;

namespace {{ package_name }}.Tests;

public class UnitsTests
{
    [Fact]
    public void ConvertsLengthWithinTheMetricSystem()
    {
        Assert.Equal(1500.0, Units.Convert(1.5, "km", "m"), 9);
        Assert.Equal(2.54, Units.Convert(1.0, "in", "cm"), 9);
    }

    [Fact]
    public void ConvertsMilesToKilometresWithTheExactFactor()
    {
        Assert.Equal(1.609344, Units.Convert(1.0, "mi", "km"), 9);
        Assert.Equal(10.0, Units.Convert(6.213711922373339, "mi", "km"), 6);
    }

    [Fact]
    public void ConvertsMassUsingTheInternationalPound()
    {
        Assert.Equal(0.45359237, Units.Convert(1.0, "lb", "kg"), 9);
    }

    [Fact]
    public void ConvertsTemperatureWithTheAffineOffsets()
    {
        Assert.Equal(212.0, Units.Convert(100.0, "C", "F"), 9);
        Assert.Equal(0.0, Units.Convert(273.15, "K", "C"), 9);
        Assert.Equal(32.0, Units.Convert(0.0, "C", "F"), 9);
        Assert.Equal(273.15, Units.Convert(0.0, "C", "K"), 9);
    }

    [Fact]
    public void TemperatureRoundTripsBackThroughItself()
    {
        Assert.Equal(98.6, Units.Convert(Units.Convert(98.6, "F", "K"), "K", "F"), 9);
    }

    [Fact]
    public void DistinguishesDecimalAndBinaryDataUnits()
    {
        Assert.Equal(1.048576, Units.Convert(1.0, "MiB", "MB"), 9);
        Assert.Equal(1024.0, Units.Convert(1.0, "KiB", "B"), 9);
    }

    [Fact]
    public void ConvertsTimeUnits()
    {
        Assert.Equal(90.0, Units.Convert(1.5, "h", "min"), 9);
        Assert.Equal(604800.0, Units.Convert(1.0, "week", "s"), 9);
    }

    [Fact]
    public void RefusesToCrossDimensions()
    {
        var error = Assert.Throws<ArgumentException>(() => Units.Convert(1.0, "km", "kg"));
        Assert.Contains("cannot convert length to mass", error.Message);
    }

    [Fact]
    public void RefusesUnknownUnits()
    {
        var error = Assert.Throws<ArgumentException>(() => Units.Lookup("furlong"));
        Assert.Contains("unknown unit: furlong", error.Message);
    }

    [Fact]
    public void UnitSymbolsAreCaseInsensitive()
    {
        Assert.Equal(1000.0, Units.Convert(1.0, "KM", "M"), 9);
        Assert.Equal("km", Units.Lookup("KM").Symbol);
        Assert.Equal(1000.0, Units.Lookup("kb").Factor, 9);
        Assert.Equal(1024.0, Units.Lookup("kib").Factor, 9);
    }

    [Fact]
    public void ListsEveryDimensionWithItsUnits()
    {
        Assert.Contains("km", Units.Symbols(Dimension.Length));
        Assert.Contains("lb", Units.Symbols(Dimension.Mass));
        Assert.Contains("F", Units.Symbols(Dimension.Temperature));
        Assert.Equal(6, Units.Dimensions.Count);
    }

    [Fact]
    public void FormatsWithoutTrailingZeroes()
    {
        Assert.Equal("6.213712", Units.Format(6.213711922373339));
        Assert.Equal("212", Units.Format(212.0));
    }
}
