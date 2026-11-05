#include "textstat/http.hpp"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <cerrno>
#include <cstdio>
#include <cstring>
#include <csignal>
#include <string_view>

#include "textstat/contract.hpp"

namespace textstat {
namespace {

constexpr std::size_t kMaxHeader = 8192;
constexpr std::size_t kMaxBody = 65536;

struct Request {
    std::string method;
    std::string path;
    std::string query;
    std::string body;
    bool malformed = false;
};

std::string lowercase(std::string_view value) {
    std::string out;
    out.reserve(value.size());
    for (char byte : value) {
        if (byte >= 'A' && byte <= 'Z') {
            out.push_back(static_cast<char>(byte - 'A' + 'a'));
        } else {
            out.push_back(byte);
        }
    }
    return out;
}

std::string trim(std::string_view value) {
    std::size_t start = 0;
    std::size_t end = value.size();
    while (start < end && (value[start] == ' ' || value[start] == '\t')) {
        ++start;
    }
    while (end > start && (value[end - 1] == ' ' || value[end - 1] == '\t' || value[end - 1] == '\r')) {
        --end;
    }
    return std::string(value.substr(start, end - start));
}

bool read_all(int fd, std::string &buffer, std::size_t limit, bool until_blank_line) {
    char chunk[4096];
    for (;;) {
        const std::string_view window = buffer;
        if (until_blank_line && window.find("\r\n\r\n") != std::string_view::npos) {
            return true;
        }
        if (buffer.size() >= limit) {
            return true;
        }
        const ssize_t got = ::recv(fd, chunk, sizeof chunk, 0);
        if (got <= 0) {
            return until_blank_line ? !buffer.empty() : true;
        }
        buffer.append(chunk, static_cast<std::size_t>(got));
    }
}

Request parse_request(std::string head, std::string body) {
    Request request;
    const std::size_t line_end = head.find("\r\n");
    const std::string_view request_line =
        std::string_view(head).substr(0, line_end == std::string::npos ? head.size() : line_end);
    const std::size_t first_space = request_line.find(' ');
    const std::size_t last_space = request_line.rfind(' ');
    if (first_space == std::string_view::npos || last_space == first_space) {
        request.malformed = true;
        return request;
    }
    request.method = std::string(request_line.substr(0, first_space));
    const std::string_view target =
        request_line.substr(first_space + 1, last_space - first_space - 1);
    const std::size_t mark = target.find('?');
    if (mark == std::string_view::npos) {
        request.path = std::string(target);
    } else {
        request.path = std::string(target.substr(0, mark));
        request.query = std::string(target.substr(mark + 1));
    }
    request.body = std::move(body);
    return request;
}

std::size_t content_length(std::string_view head) {
    std::size_t start = 0;
    while (start < head.size()) {
        std::size_t end = head.find("\r\n", start);
        if (end == std::string_view::npos) {
            break;
        }
        const std::string_view line = head.substr(start, end - start);
        const std::size_t colon = line.find(':');
        if (colon != std::string_view::npos &&
            lowercase(line.substr(0, colon)) == "content-length") {
            const std::string value = trim(line.substr(colon + 1));
            try {
                return static_cast<std::size_t>(std::stoul(value));
            } catch (...) {
                return 0;
            }
        }
        start = end + 2;
    }
    return 0;
}

const char *reason(int status) {
    switch (status) {
        case 200: return "OK";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 413: return "Content Too Large";
        case 422: return "Unprocessable Entity";
        default: return "Internal Server Error";
    }
}

void respond(int fd, int status, std::string_view body) {
    std::string head = "HTTP/1.1 " + std::to_string(status) + " " + reason(status) + "\r\n";
    head += "content-type: application/json\r\n";
    head += "content-length: " + std::to_string(body.size()) + "\r\n";
    head += "connection: close\r\n\r\n";
    std::string payload = head;
    payload += body;
    std::size_t sent = 0;
    while (sent < payload.size()) {
        const ssize_t wrote = ::send(fd, payload.data() + sent, payload.size() - sent, 0);
        if (wrote <= 0) {
            return;
        }
        sent += static_cast<std::size_t>(wrote);
    }
}

void handle(int fd) {
    std::string buffer;
    if (!read_all(fd, buffer, kMaxHeader, true)) {
        respond(fd, 413, "{\"error\":\"body_too_large\"}");
        return;
    }
    const std::size_t split = buffer.find("\r\n\r\n");
    if (split == std::string::npos) {
        respond(fd, 422, "{\"error\":\"bad_request\"}");
        return;
    }
    const std::string head = buffer.substr(0, split + 2);
    std::string body = buffer.substr(split + 4);
    const std::size_t length = content_length(head);
    if (length > kMaxBody) {
        respond(fd, 413, "{\"error\":\"body_too_large\"}");
        return;
    }
    while (body.size() < length) {
        char chunk[4096];
        const ssize_t got = ::recv(fd, chunk, sizeof chunk, 0);
        if (got <= 0) {
            break;
        }
        body.append(chunk, static_cast<std::size_t>(got));
    }
    if (body.size() > length) {
        body.resize(length);
    }
    const Request request = parse_request(head, body);
    if (request.malformed) {
        respond(fd, 422, "{\"error\":\"bad_request\"}");
        return;
    }
    const Reply reply = route(request.method, request.path, request.query, request.body);
    respond(fd, reply.status, reply.body);
}

}  // namespace

int serve(const std::string &host, int port) {
    std::signal(SIGPIPE, SIG_IGN);
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<unsigned short>(port));
    if (::inet_pton(AF_INET, host.c_str(), &address.sin_addr) != 1) {
        std::fprintf(stderr, "invalid host %s\n", host.c_str());
        return 2;
    }
    const int listener = ::socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) {
        std::perror("socket");
        return 1;
    }
    const int reuse = 1;
    ::setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
    timeval timeout{5, 0};
    ::setsockopt(listener, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
    if (::bind(listener, reinterpret_cast<sockaddr *>(&address), sizeof address) < 0) {
        std::perror("bind");
        ::close(listener);
        return 1;
    }
    if (::listen(listener, 16) < 0) {
        std::perror("listen");
        ::close(listener);
        return 1;
    }
    std::printf("listening on http://%s:%d\n", host.c_str(), port);
    std::fflush(stdout);
    for (;;) {
        const int client = ::accept(listener, nullptr, nullptr);
        if (client < 0) {
            if (errno == EINTR) {
                continue;
            }
            std::perror("accept");
            ::close(listener);
            return 1;
        }
        handle(client);
        ::close(client);
    }
}

}  // namespace textstat
