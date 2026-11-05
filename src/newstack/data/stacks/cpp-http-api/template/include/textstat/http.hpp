#ifndef TEXTSTAT_HTTP_HPP
#define TEXTSTAT_HTTP_HPP

#include <string>

namespace textstat {

// Serves one request per connection until the process is killed. Returns a
// non-zero value only when the listener could not be set up at all.
int serve(const std::string &host, int port);

}  // namespace textstat

#endif
