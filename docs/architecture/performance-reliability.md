# Performance & Reliability

- Caching: local caches for resources; LRU for vector queries.
- Concurrency: rate‑limit and shard large cascades.
- Idempotency: keys on executions; retries with backoff; partial rollback on failure.
- Load goals: ≥100 projects, 10–20 personas each, ≥10k docs/collection.
