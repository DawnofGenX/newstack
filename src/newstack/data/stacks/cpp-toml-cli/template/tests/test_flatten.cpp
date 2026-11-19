#include "toml/flatten.h"

#include <cassert>
#include <iostream>
#include <string>

int main() {
    std::string input = "[server]\nhost = \"localhost\"\nport = 8080\n";
    std::string out = toml_flatten(input);
    std::string expected = "server.host = \"localhost\"\nserver.port = 8080\n";
    if (out != expected) {
        std::cerr << "expected:\n" << expected << "got:\n" << out << "\n";
        return 1;
    }
    // top-level
    std::string t = toml_flatten("name = \"x\"\n");
    if (t != "name = \"x\"\n") {
        std::cerr << "top-level failed: " << t << "\n";
        return 1;
    }
    // empty
    if (toml_flatten("") != "") {
        std::cerr << "empty failed\n";
        return 1;
    }
    std::cout << "all checks passed\n";
    return 0;
}