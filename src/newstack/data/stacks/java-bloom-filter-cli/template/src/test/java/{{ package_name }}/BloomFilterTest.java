package {{ package_name }};

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BloomFilterTest {
    @Test
    void containsInserted() {
        BloomFilter bf = new BloomFilter(100, 0.01);
        for (int i = 0; i < 50; i++) bf.add("item" + i);
        for (int i = 0; i < 50; i++) assertTrue(bf.contains("item" + i));
    }

    @Test
    void emptyFilter() {
        BloomFilter bf = new BloomFilter(8, 2);
        assertFalse(bf.contains("nope"));
    }

    @Test
    void invalidArgs() {
        assertThrows(IllegalArgumentException.class, () -> new BloomFilter(0, 0.01));
    }
}
