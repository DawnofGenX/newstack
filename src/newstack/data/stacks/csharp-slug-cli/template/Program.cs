// csharp-slug-cli

using System.Text;

namespace {{ package_name }};

class Program
{
    static int Main(string[] args)
    {
        string? input = null;
        string separator = "-";
        int max = 0;
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--separator":
                    separator = args[++i];
                    break;
                case "--max":
                    max = int.Parse(args[++i]);
                    break;
                default:
                    input = input is null ? args[i] : input + " " + args[i];
                    break;
            }
        }
        if (input is null)
        {
            input = Console.In.ReadToEnd();
        }
        Console.WriteLine(Slugger.Slugify(input, separator, max));
        return 0;
    }
}

public static class Slugger
{
    public static string Slugify(string text, string separator = "-", int maxLength = 0)
    {
        if (text is null) return string.Empty;
        var sb = new StringBuilder();
        bool prevSep = true;
        foreach (char c in text.ToLowerInvariant())
        {
            if (char.IsLetterOrDigit(c))
            {
                sb.Append(c);
                prevSep = false;
            }
            else if (!prevSep)
            {
                sb.Append(separator);
                prevSep = true;
            }
        }
        var result = sb.ToString().Trim(separator.ToCharArray());
        if (maxLength > 0 && result.Length > maxLength)
        {
            result = result[..maxLength].TrimEnd(separator.ToCharArray());
        }
        return result;
    }
}
