#include "toml/flatten.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

static std::string read_all(std::istream &in) {
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a == "-h" || a == "--help") {
            std::cout << "Usage: toml-flatten [FILE...]\n";
            std::cout << "Flatten a TOML subset document into key = value lines.\n";
            return 0;
        }
        if (a == "-v" || a == "--version") {
            std::cout << "toml-flatten 1.0.0\n";
            return 0;
        }
        if (a.rfind("-", 0) == 0 && a != "-") {
            std::cerr << "toml-flatten: unknown option '" << a << "'\n";
            return 2;
        }
    }
    bool any_file = false;
    int rc = 0;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a.rfind("-", 0) == 0 && a != "-") continue;
        any_file = true;
        std::istream *in = &std::cin;
        std::ifstream f;
        if (a != "-") {
            f.open(a);
            if (!f) {
                std::cerr << "toml-flatten: cannot open '" << a << "'\n";
                rc = 1;
                continue;
            }
            in = &f;
        }
        std::string content = read_all(*in);
        std::cout << toml_flatten(content);
    }
    if (!any_file) {
        std::string content = read_all(std::cin);
        std::cout << toml_flatten(content);
    }
    return rc;
}