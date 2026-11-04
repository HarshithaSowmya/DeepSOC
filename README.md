# DeepSOC

AI-assisted Security Operations Center built with **Python, FastAPI, Apache Kafka, scikit-learn and SQLite**. A responsive dashboard monitors real model output, investigates alerts and manages incidents. No frontend build step is required.

## Run locally (Windows PowerShell)

Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:SOC_MODE = "demo"
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000**. API explorer: **http://127.0.0.1:8000/docs**.

Demo mode generates synthetic traffic, scores it with Isolation Forest and persists detections. Use **Simulate threat** to submit a known synthetic attack. Search and filter alerts, inspect raw events, export CSV, update incident status or simulate an IP block. Responses do not modify a firewall or user directory.

Optional settings are listed in `.env.example`. Uvicorn does not automatically load that file: use environment variables or `uvicorn app.main:app --env-file .env` after copying the example. Set `API_KEY` before using real telemetry. Enter the same key in the dashboard's **API access** dialog; the browser keeps it only for that tab. All `/api/` endpoints require the key when configured. Health checks and frontend assets remain public.

## Full Kafka stack

With Docker Engine running:

```powershell
docker compose up --build -d
```

Open http://127.0.0.1:8000. Compose starts the API, Kafka broker and detection worker; the API and worker share a SQLite volume. Kafka uses separate internal and host listeners. The dashboard shows **Kafka mode**; synthetic background traffic is disabled. Submit events using the dashboard or API.

For local Python development with Kafka, start only the broker (`docker compose up -d kafka`), set `SOC_MODE=kafka` and `KAFKA_BOOTSTRAP=localhost:9092`, then start Uvicorn and `python -m app.worker` in separate terminals using the same `DB_PATH`.

The API reuses its producer and waits for broker acknowledgment before accepting a log. The worker commits offsets after processing. Delivery is at least once: replay after a crash may create duplicate alerts. This single-node portfolio architecture is not a highly available production cluster. SQLite is shared only within one host; use a transactional server database and idempotent event processing before scaling across hosts.

## Deployment

See [deployment instructions](docs/deployment.md).

- **Render:** simplest shareable demo; `render.yaml` runs the Docker image in demo mode, generates an API key and checks `/health`. Retrieve the generated key from Render's environment settings, then enter it in **API access**. The free blueprint has ephemeral storage: restarts/redeploys can reset data. A persistent disk requires an eligible paid service.
- **Linux server:** `docker compose up --build -d` runs the complete Kafka platform. Put an HTTPS reverse proxy in front of the loopback API port and configure `API_KEY`.

## Validation

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest -q
node --check static/app.js
docker compose config --quiet
```

GitHub Actions runs these checks and builds the Docker image on pushes and pull requests.

## Evaluation and performance targets

The requested 100,000+ logs, 10,000+ events/min, 95% accuracy, 35% fewer false positives, 60% faster response and 40% performance improvement are **targets, not verified guarantees**. No controlled before/after baseline is included. Historical figures from the supplied ZIP are identified in [evaluation notes](docs/evaluation.md); they are not validation of this version or real-world threat accuracy.

```powershell
.\.venv\Scripts\python -m scripts.evaluate_accuracy --count 20000
.\.venv\Scripts\python -m scripts.benchmark_pipeline --count 20000 --persist
```

Run persistence benchmarks with a separate `DB_PATH` to keep synthetic benchmark records out of the dashboard. Producer-only benchmarks do not measure end-to-end pipeline capacity.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/health` | API and transport health (not worker-lag monitoring) |
| GET | `/api/metrics` | Persistent totals, severity counts, rolling activity |
| POST | `/api/logs` | Validate and ingest one security event |
| GET | `/api/alerts?limit=100` | Latest alerts (maximum 500) |
| GET | `/api/incidents?limit=100` | Latest incidents (maximum 500) |
| PATCH | `/api/incidents/{id}` | Update status and linked alert |
| POST | `/api/incidents/{id}/respond` | Simulate block_ip or disable_account |

Dashboard tables show a bounded latest-record window; the summary metrics use all stored records. Activity uses processing-time minute buckets. The displayed last-minute rate is estimated across adjacent buckets. Scores measure distance from the model's baseline, not confidence percentages.
