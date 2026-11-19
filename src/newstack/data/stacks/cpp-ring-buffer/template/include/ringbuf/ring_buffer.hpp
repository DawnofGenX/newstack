#ifndef RINGBUF_RING_BUFFER_HPP
#define RINGBUF_RING_BUFFER_HPP

#include <array>
#include <cstddef>
#include <optional>

namespace ringbuf {

template <typename T, std::size_t Capacity>
class RingBuffer {
    static_assert(Capacity > 0, "capacity must be positive");
    std::array<T, Capacity> data_{};
    std::size_t head_ = 0;
    std::size_t tail_ = 0;
    std::size_t size_ = 0;

public:
    bool push(const T &value) {
        if (size_ == Capacity) return false;
        data_[tail_] = value;
        tail_ = (tail_ + 1) % Capacity;
        ++size_;
        return true;
    }

    bool pop(T &out) {
        if (size_ == 0) return false;
        out = data_[head_];
        head_ = (head_ + 1) % Capacity;
        --size_;
        return true;
    }

    bool peek(T &out) const {
        if (size_ == 0) return false;
        out = data_[head_];
        return true;
    }

    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    bool full() const { return size_ == Capacity; }
    static constexpr std::size_t capacity() { return Capacity; }
};

} // namespace ringbuf

#endif
