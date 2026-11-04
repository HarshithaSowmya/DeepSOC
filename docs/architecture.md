# Architecture

Browser dashboard → FastAPI ingestion → Apache Kafka security-logs topic → Python detection worker → Isolation Forest → SQLite alerts + incidents → simulated analyst response.

Demo deployment replaces Kafka and the separate worker with an in-process synthetic event generator. The detector and persistence path are shared. Demo detection runs in a thread so scoring does not block the API event loop.

The API holds a reusable Kafka producer with all-replica acknowledgments and gzip compression. The worker persists processing counters, traffic buckets, alerts and incidents in a single SQLite transaction, then commits its Kafka offset. Processing is at least once; alert deduplication is not implemented. Compose API and worker mount the same database volume; standalone distributed hosts need a server database.

SQLite uses WAL and a busy timeout. Persistent counters and time buckets power the UI; totals survive API restarts while the database survives. Alert/incident status updates share transactions. Optional API-key protection covers every data endpoint.

Incident playbooks simulate blocking an IP or disabling an account and record that simulation. They do not perform external infrastructure changes. Automated policy execution and production response adapters remain future work.
