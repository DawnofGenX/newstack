package {{ package_name }};

import java.util.BitSet;

public final class BloomFilter {
    private final int m;
    private final int k;
    private final BitSet bits;

    public BloomFilter(int expectedInsertions, double fpp) {
        if (expectedInsertions <= 0) throw new IllegalArgumentException("expectedInsertions must be positive");
        int mm = (int) Math.ceil(-(expectedInsertions * Math.log(fpp)) / (Math.log(2) * Math.log(2)));
        int kk = (int) Math.ceil((mm / (double) expectedInsertions) * Math.log(2));
        if (kk < 1) kk = 1;
        this.m = mm;
        this.k = kk;
        this.bits = new BitSet(mm);
    }

    public BloomFilter(int m, int k) {
        if (m <= 0 || k <= 0) throw new IllegalArgumentException("m and k must be positive");
        this.m = m;
        this.k = k;
        this.bits = new BitSet(m);
    }

    public void add(String value) {
        for (int i = 0; i < k; i++) bits.set(hash(value, i) % m);
    }

    public boolean contains(String value) {
        for (int i = 0; i < k; i++) if (!bits.get(hash(value, i) % m)) return false;
        return true;
    }

    public int size() { return m; }

    private int hash(String value, int seed) {
        int h = value.hashCode() ^ (seed * 0x9e3779b9);
        h ^= (h >>> 16);
        return Math.abs(h);
    }
}
