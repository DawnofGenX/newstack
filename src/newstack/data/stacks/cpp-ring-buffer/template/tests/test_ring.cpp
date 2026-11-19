#include "ringbuf/ring_buffer.hpp"

#include <cassert>
#include <iostream>

int main() {
    ringbuf::RingBuffer<int, 4> rb;
    assert(rb.empty());
    assert(rb.push(1));
    assert(rb.push(2));
    assert(rb.size() == 2);
    int v = 0;
    assert(rb.peek(v) && v == 1);
    assert(rb.pop(v) && v == 1);
    assert(rb.pop(v) && v == 2);
    assert(rb.empty());
    assert(rb.push(10));
    assert(rb.push(20));
    assert(rb.push(30));
    assert(rb.push(40));
    assert(rb.full());
    assert(!rb.push(50));
    assert(rb.pop(v) && v == 10);
    assert(rb.push(50));
    assert(rb.pop(v) && v == 20);
    std::cout << "all checks passed\n";
    return 0;
}
