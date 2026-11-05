# Retry policy

A write is retried only when the failure is retryable: connection reset, timeout,
and the two status codes that mean "try again" (429 and 503). A 500 is not retried,
because repeating a request the server already failed to handle usually repeats the
failure and doubles the load.

Backoff is exponential with full jitter, capped at eight seconds. The attempt count
is part of the request id, so a duplicate arriving late is recognised and answered
with the original result rather than applied twice. Retried writes must be
idempotent: the client sends the same idempotency key on every attempt, and the
store keeps that key for twenty-four hours after the first attempt succeeded.

The queue drains in order within a partition. A retry re-enters at the back of the
retry lane, not the back of the main lane, so one slow tenant cannot delay a
healthy one.
