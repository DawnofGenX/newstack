// csharp-units-cli

using System.Globalization;

namespace {{ package_name }};

public enum Dimension
{
    Length,
    Mass,
    Volume,
    Time,
    Data,
    Temperature,
}

public sealed record Unit(string Symbol, Dimension Kind, double Factor)
{
    /// <summary>Convert this unit's value into the dimension's base unit (m, kg, l, s, byte).</summary>
    public double ToBase(double value) =>
        Kind == Dimension.Temperature ? value : value * Factor;
}

public static class Units
{
    private static readonly Dictionary<string, Unit> Registry = Build();

    private static Dictionary<string, Unit> Build()
    {
        var table = new Dictionary<string, Unit>(StringComparer.OrdinalIgnoreCase);
        void Add(Unit unit) => table[unit.Symbol] = unit;
        void AddAll(Dimension dimension, params (string Symbol, double Factor)[] entries)
        {
            foreach (var (symbol, factor) in entries)
            {
                Add(new Unit(symbol, dimension, factor));
            }
        }

        AddAll(Dimension.Length,
            ("m", 1.0), ("km", 1000.0), ("cm", 0.01), ("mm", 0.001),
            ("mi", 1609.344), ("yd", 0.9144), ("ft", 0.3048), ("in", 0.0254), ("nmi", 1852.0));
        AddAll(Dimension.Mass,
            ("kg", 1.0), ("g", 0.001), ("mg", 0.000001), ("t", 1000.0),
            ("lb", 0.45359237), ("oz", 0.028349523125), ("st", 6.35029318));
        AddAll(Dimension.Volume,
            ("l", 1.0), ("ml", 0.001), ("m3", 1000.0), ("gal", 3.785411784),
            ("qt", 0.946352946), ("pt", 0.473176473), ("cup", 0.2365882365), ("floz", 0.0295735295625));
        AddAll(Dimension.Time,
            ("s", 1.0), ("ms", 0.001), ("us", 0.000001), ("min", 60.0),
            ("h", 3600.0), ("day", 86400.0), ("week", 604800.0));
        AddAll(Dimension.Data,
            ("B", 1.0), ("kB", 1000.0), ("KiB", 1024.0), ("MB", 1000000.0), ("MiB", 1048576.0),
            ("GB", 1000000000.0), ("GiB", 1073741824.0), ("TB", 1000000000000.0));
        AddAll(Dimension.Temperature, ("C", 1.0), ("F", 1.0), ("K", 1.0));
        return table;
    }

    public static IEnumerable<string> Symbols(Dimension dimension) =>
        Registry.Where(pair => pair.Value.Kind == dimension).Select(pair => pair.Key);

    public static IReadOnlyList<Dimension> Dimensions => Enum.GetValues<Dimension>();

    public static Unit Lookup(string symbol) =>
        Registry.TryGetValue(symbol, out var unit)
            ? unit
            : throw new ArgumentException($"unknown unit: {symbol}");

    public static double Convert(double value, string from, string to)
    {
        var source = Lookup(from);
        var target = Lookup(to);
        if (source.Kind != target.Kind)
        {
            throw new ArgumentException($"cannot convert {source.Kind.ToString().ToLowerInvariant()} to {target.Kind.ToString().ToLowerInvariant()}");
        }
        return source.Kind switch
        {
            Dimension.Temperature => ConvertTemperature(value, from, to),
            _ => target.Factor == 0 ? throw new ArgumentException("zero factor") : source.ToBase(value) / target.Factor,
        };
    }

    private static double ConvertTemperature(double value, string from, string to)
    {
        double celsius = from.ToUpperInvariant() switch
        {
            "C" => value,
            "F" => (value - 32.0) * 5.0 / 9.0,
            "K" => value - 273.15,
            _ => throw new ArgumentException($"unknown unit: {from}"),
        };
        return to.ToUpperInvariant() switch
        {
            "C" => celsius,
            "F" => celsius * 9.0 / 5.0 + 32.0,
            "K" => celsius + 273.15,
            _ => throw new ArgumentException($"unknown unit: {to}"),
        };
    }

    public static string Format(double value) => value.ToString("0.######", CultureInfo.InvariantCulture);
}
