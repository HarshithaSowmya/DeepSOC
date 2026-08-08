# Architecture

FastAPI receives normalized security events and publishes them to Kafka.
The AI worker consumes the stream and uses Isolation Forest for unsupervised
anomaly detection. Anomalies become alerts and incidents stored in SQLite.
Automated response is simulated for portfolio safety.

Production extensions:
- PostgreSQL
- OpenSearch/Elasticsearch
- Redis
- Prometheus/Grafana
- JWT/RBAC
- Sigma rules
- MITRE ATT&CK mapping
- React dashboard
- Real authorized firewall/EDR/SOAR integrations
