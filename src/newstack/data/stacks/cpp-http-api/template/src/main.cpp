#include <cstdio>
#include <cstdlib>
#include <string>

#include "textstat/http.hpp"

namespace {

int port_from_env() {
    const char *raw = std::getenv("PORT");
    if (raw == nullptr || *raw == '\0') {
        return 8080;
    }
    return std::atoi(raw);
}

std::string host_from_env() {
    const char *raw = std::getenv("HOST");
    if (raw == nullptr || *raw == '\0') {
        return "127.0.0.1";
    }
    return raw;
}

}  // namespace

int main() {
    return textstat::serve(host_from_env(), port_from_env());
}
