#include "ringbuf/ring_buffer.hpp"

#include <iostream>
#include <sstream>
#include <string>

int main(int argc, char **argv) {
    if (argc > 1) {
        std::string arg = argv[1];
        if (arg == "--help" || arg == "-h") {
            std::cout << "Usage: " << (argc > 0 ? argv[0] : "ringbuf") << "\n";
            std::cout << "Trace-driven fixed-capacity (8) ring buffer.\n";
            std::cout << "Commands: push N, pop, peek, size\n";
            return 0;
        }
        if (arg == "--version") {
            std::cout << "0.1.0\n";
            return 0;
        }
        std::cerr << "unknown option: " << arg << "\n";
        return 2;
    }

    ringbuf::RingBuffer<int, 8> buffer;
    std::string line;
    while (std::getline(std::cin, line)) {
        std::istringstream in(line);
        std::string cmd;
        in >> cmd;
        if (cmd.empty() || cmd == "quit" || cmd == "exit") continue;
        if (cmd == "push") {
            int value;
            if (!(in >> value)) {
                std::cerr << "usage: push N\n";
                return 2;
            }
            if (buffer.push(value)) std::cout << "pushed " << value << "\n";
            else std::cout << "full\n";
        } else if (cmd == "pop") {
            int value;
            if (buffer.pop(value)) std::cout << "popped " << value << "\n";
            else std::cout << "empty\n";
        } else if (cmd == "peek") {
            int value;
            if (buffer.peek(value)) std::cout << "peek " << value << "\n";
            else std::cout << "empty\n";
        } else if (cmd == "size") {
            std::cout << buffer.size() << "\n";
        } else {
            std::cerr << "unknown command: " << cmd << "\n";
            return 2;
        }
    }
    return 0;
}
