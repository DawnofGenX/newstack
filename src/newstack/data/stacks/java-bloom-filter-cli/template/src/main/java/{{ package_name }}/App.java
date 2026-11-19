package {{ package_name }};

import java.io.PrintWriter;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class App {
    public static void main(String[] args) throws Exception {
        System.exit(run(args, new java.io.InputStreamReader(System.in), new PrintWriter(System.out, true), new PrintWriter(System.err, true)));
    }

    public static int run(String[] args, Reader in, PrintWriter out, PrintWriter err) throws Exception {
        if (args.length == 0 || args[0].equals("-h") || args[0].equals("--help")) {
            out.print(usage());
            out.flush();
            return 0;
        }
        if (!args[0].equals("contains")) {
            err.println("unknown command: " + args[0]);
            return 2;
        }
        if (args.length < 2) {
            err.println("contains needs an item");
            return 2;
        }
        String item = args[1];
        String membersFile = null;
        for (int i = 2; i < args.length; i++) {
            if (args[i].equals("--members") && i + 1 < args.length) {
                membersFile = args[++i];
            }
        }
        List<String> members = new ArrayList<>();
        if (membersFile != null) {
            java.nio.file.Path p = java.nio.file.Paths.get(membersFile);
            for (String line : java.nio.file.Files.readAllLines(p, java.nio.charset.StandardCharsets.UTF_8)) {
                if (!line.trim().isEmpty()) members.add(line.trim());
            }
        } else {
            Scanner sc = new Scanner(in);
            while (sc.hasNextLine()) {
                String line = sc.nextLine().trim();
                if (!line.isEmpty()) members.add(line);
            }
        }
        BloomFilter bf;
        if (members.isEmpty()) {
            bf = new BloomFilter(8, 2);
        } else {
            bf = new BloomFilter(Math.max(1, members.size()), 0.01);
            if (bf.size() < 8) bf = new BloomFilter(8, 2);
        }
        for (String m : members) bf.add(m);
        boolean present = bf.contains(item);
        out.println(present ? "probably" : "no");
        out.flush();
        return 0;
    }

    private static String usage() {
        return "usage: {{ npm_name }} contains ITEM [--members FILE]\n\nBloom filter membership test.\nExit codes: 0 success, 1 bad input, 2 usage error.\n";
    }
}
