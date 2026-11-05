# Rebalancing shards

A shard owns a contiguous range of the hash ring. When a node fails, its shards are
marked unavailable rather than reassigned immediately: the failure may be a network
partition, and moving data onto a live node while the old one is still serving
writes creates two histories for the same range.

After the failure is confirmed, the controller picks up the orphaned shards and
assigns each to the live node with the fewest bytes, measured after the move
completes rather than before. A rebalance is throttled to one shard per node at a
time; the copy is a snapshot plus a replay of the write-ahead log, and the range is
only reopened for writes when the replay reaches the snapshot's sequence number.

Rebalancing by count instead of bytes is the classic mistake: shards in a busy range
are two orders of magnitude larger than shards in a quiet one, so an even count
leaves the busiest node the busiest node still.
