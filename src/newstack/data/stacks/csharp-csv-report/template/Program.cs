using System.Text.Json;

namespace {{ package_name }};

class Program
{
    static int Main(string[] args)
    {
        string? inputPath = null;
        string groupColumn = "department";
        bool json = false;
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--json")
            {
                json = true;
            }
            else if (args[i] == "--group")
            {
                groupColumn = args[++i];
            }
            else
            {
                inputPath = args[i];
            }
        }

        string text = inputPath is null
            ? Console.In.ReadToEnd()
            : File.ReadAllText(inputPath);

        var csv = Csv.Parse(text);
        var rows = Report.Build(csv, groupColumn);

        if (json)
        {
            Console.WriteLine(JsonSerializer.Serialize(rows));
        }
        else
        {
            Console.Write(Report.RenderTable(rows));
        }
        return 0;
    }
}
