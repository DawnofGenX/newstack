// csharp-diff-cli

using System.Text;

namespace {{ package_name }};

public static class Cli
{
    public static int Run(string[] args) => Run(args, Console.In, Console.Out, Console.Error);

    public static int Run(string[] args, TextReader input, TextWriter output, TextWriter error)
    {
        int context = 3;
        string? oldFile = null;
        string? newFile = null;
        var positional = new List<string>();
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--context":
                case "-U":
                    if (i + 1 >= args.Length) { error.WriteLine("missing value for --context"); return 2; }
                    if (!int.TryParse(args[++i], out context) || context < 0) { error.WriteLine("bad context"); return 2; }
                    break;
                case "--old":
                    if (i + 1 >= args.Length) { error.WriteLine("missing value for --old"); return 2; }
                    oldFile = args[++i];
                    break;
                case "--new":
                    if (i + 1 >= args.Length) { error.WriteLine("missing value for --new"); return 2; }
                    newFile = args[++i];
                    break;
                case "-h":
                case "--help":
                    output.WriteLine("usage: {{ npm_name }} OLD NEW [--context N]");
                    return 0;
                default:
                    positional.Add(args[i]);
                    break;
            }
        }
        if (oldFile is null && positional.Count >= 1) oldFile = positional[0];
        if (newFile is null && positional.Count >= 2) newFile = positional[1];
        if (oldFile is null || newFile is null)
        {
            error.WriteLine("need two inputs");
            return 2;
        }

        string oldText, newText;
        try
        {
            oldText = oldFile == "-" ? input.ReadToEnd() : File.ReadAllText(oldFile);
            newText = newFile == "-" ? input.ReadToEnd() : File.ReadAllText(newFile);
        }
        catch (Exception ex)
        {
            error.WriteLine("cannot read input: " + ex.Message);
            return 1;
        }

        var result = Differ.Unified(oldText, newText, context);
        output.Write(result);
        if (!result.EndsWith("\n")) output.WriteLine();
        return 0;
    }
}

public static class Differ
{
    public static string[] SplitLines(string text)
    {
        if (text is null) return Array.Empty<string>();
        return text.Replace("\r\n", "\n").Split('\n');
    }

    // Compute edit operations: 0 = common, -1 = removed (from a), +1 = added (from b)
    public static List<(int op, string line)> Diff(string[] a, string[] b)
    {
        int n = a.Length, m = b.Length;
        var dp = new int[n + 1, m + 1];
        for (int i = n - 1; i >= 0; i--)
            for (int j = m - 1; j >= 0; j--)
                if (a[i] == b[j]) dp[i, j] = 1 + dp[i + 1, j + 1];
                else dp[i, j] = Math.Max(dp[i + 1, j], dp[i, j + 1]);

        var ops = new List<(int, string)>();
        int x = 0, y = 0;
        while (x < n && y < m)
        {
            if (a[x] == b[y]) { ops.Add((0, a[x])); x++; y++; }
            else if (dp[x + 1, y] >= dp[x, y + 1]) { ops.Add((-1, a[x])); x++; }
            else { ops.Add((1, b[y])); y++; }
        }
        while (x < n) { ops.Add((-1, a[x])); x++; }
        while (y < m) { ops.Add((1, b[y])); y++; }
        return ops;
    }

    public static string Unified(string oldText, string newText, int context)
    {
        var a = SplitLines(oldText);
        var b = SplitLines(newText);
        // trim trailing empty line produced by trailing newline
        if (a.Length > 0 && a[^1] == string.Empty && oldText.EndsWith("\n")) a = a[..^1];
        if (b.Length > 0 && b[^1] == string.Empty && newText.EndsWith("\n")) b = b[..^1];

        var ops = Diff(a, b);
        if (ops.All(o => o.op == 0))
        {
            return "--- a\n+++ b\n";
        }

        // Build hunks
        var sb = new StringBuilder();
        sb.AppendLine("--- a");
        sb.AppendLine("+++ b");

        // identify ranges of changes
        int i = 0;
        int nops = ops.Count;
        while (i < nops)
        {
            // skip common until next change within context
            if (ops[i].op == 0)
            {
                // check if a change follows within context
                int j = i;
                bool changeSoon = false;
                for (int k = i; k < Math.Min(nops, i + context + 1); k++)
                {
                    if (ops[k].op != 0) { changeSoon = true; break; }
                }
                if (!changeSoon) { i++; continue; }
            }
            // start hunk
            int start = Math.Max(0, i - context);
            // extend
            int end = i;
            // find end of change block: include trailing context until next change gap > 2*context+1
            int cursor = i;
            // We'll iterate to build hunk end
            int hunkEnd = i;
            // move cursor through ops, including context after each change
            int lastChange = i;
            int p = i;
            // determine hunk range [start, endExclusive)
            // start already
            // find last op index to include
            int last = i;
            // walk forward
            int idx = i;
            while (idx < nops)
            {
                // if common gap larger than 2*context, stop
                if (ops[idx].op == 0)
                {
                    // count run of common
                    int runStart = idx;
                    while (idx < nops && ops[idx].op == 0) idx++;
                    int runLen = idx - runStart;
                    if (runLen > 2 * context && idx < nops && ops.Skip(idx).Any(o => o.op != 0))
                    {
                        // stop before this gap, keep 'context' trailing
                        last = Math.Min(nops, runStart + context);
                        break;
                    }
                    last = idx;
                    if (idx >= nops) break;
                }
                else
                {
                    last = idx + 1;
                    idx++;
                }
            }
            int hunkStart = Math.Max(0, start);
            int hunkEndExcl = Math.Min(nops, last);
            // compute line numbers
            int oldLine = 1, newLine = 1;
            for (int t = 0; t < hunkStart; t++)
            {
                if (ops[t].op <= 0) oldLine++;
                if (ops[t].op >= 0) newLine++;
            }
            int oldCount = 0, newCount = 0;
            for (int t = hunkStart; t < hunkEndExcl; t++)
            {
                if (ops[t].op <= 0) oldCount++;
                if (ops[t].op >= 0) newCount++;
            }
            sb.AppendLine($"@@ -{oldLine},{oldCount} +{newLine},{newCount} @@");
            for (int t = hunkStart; t < hunkEndExcl; t++)
            {
                var (op, line) = ops[t];
                if (op == 0) sb.AppendLine(" " + line);
                else if (op < 0) sb.AppendLine("-" + line);
                else sb.AppendLine("+" + line);
            }
            i = hunkEndExcl;
            // skip common gap
            while (i < nops && ops[i].op == 0) i++;
        }
        return sb.ToString();
    }
}
