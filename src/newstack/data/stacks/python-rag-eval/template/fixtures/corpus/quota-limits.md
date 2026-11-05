# Quota limits

Each tenant has a request limit per minute and a burst allowance. The limiter is a
token bucket: the bucket refills at the per-minute rate divided by sixty, holds at
most the burst, and is charged one token per request regardless of size. A request
that finds fewer than one token is refused with 429, a Retry-After header, and no
side effect.

The bucket lives next to the tenant's data rather than in the gateway, so several
gateways cannot each spend the same allowance. Reads and writes draw from the same
bucket; an earlier design split them and a tenant with a generous write limit
exhausted the read path with retries.

Limits are per tenant, not per key: adding a second key to a tenant does not add a
second allowance, which is the difference between a quota and a suggestion.
