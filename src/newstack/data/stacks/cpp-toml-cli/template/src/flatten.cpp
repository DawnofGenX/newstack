#include "toml/flatten.h"

#include <sstream>
#include <string>
#include <vector>

static std::string trim(const std::string &s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

std::string toml_flatten(const std::string &input) {
    std::istringstream in(input);
    std::string line;
    std::string section;
    std::ostringstream out;
    while (std::getline(in, line)) {
        std::string t = trim(line);
        if (t.empty() || t[0] == '#') continue;
        if (t.front() == '[' && t.back() == ']') {
            section = trim(t.substr(1, t.size() - 2));
            continue;
        }
        size_t eq = t.find('=');
        if (eq == std::string::npos) continue;
        std::string key = trim(t.substr(0, eq));
        std::string val = trim(t.substr(eq + 1));
        std::string full = section.empty() ? key : section + "." + key;
        out << full << " = " << val << "\n";
    }
    return out.str();
}