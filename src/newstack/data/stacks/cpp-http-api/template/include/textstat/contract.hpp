#ifndef TEXTSTAT_CONTRACT_HPP
#define TEXTSTAT_CONTRACT_HPP

#include <string>
#include <string_view>

namespace textstat {

// One answer: the status line to send and the JSON body to send with it.
struct Reply {
    int status = 200;
    std::string body;
};

// Pure: everything the request carries comes in as a string, and the answer
// comes back as data. The socket layer never needs to know the rules.
Reply route(std::string_view method, std::string_view path, std::string_view query,
            std::string_view body);

}  // namespace textstat

#endif
