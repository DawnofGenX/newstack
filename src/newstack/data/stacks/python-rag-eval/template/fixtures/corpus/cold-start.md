# Cold start

The first request to a fresh process pays for three things: importing the modules,
opening the connection pool, and filling the certificate cache. Only the first is
visible in the request latency; the pool opens lazily on the first query, so the
second request is the slow one even though the first request looks worse in a log.

Warm-up therefore does a single query and a single handshake before the process is
marked ready, and readiness is reported through the health endpoint rather than a
sleep. A process that answers health before its pool is open takes traffic it
cannot serve, which is a self-inflicted outage on every deploy.

The benchmark reports the first request, the second request, and the steady state
separately. Averaging them hides the only number that matters during a rolling
deploy.
