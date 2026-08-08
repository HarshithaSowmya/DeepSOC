# AI Integrated SOC Detection & Response Platform

Portfolio-ready SOC project using Python, FastAPI, Apache Kafka and scikit-learn.

## Flow
Security Logs -> Kafka -> AI Anomaly Detection -> Alerts -> Incidents -> Automated Response

## Run
1. Start Kafka:
   `docker compose up -d`
2. Create environment:
   `python -m venv .venv`
3. Activate it and install:
   `pip install -r requirements.txt`
4. Start API:
   `uvicorn app.main:app --reload`
5. Start worker in another terminal:
   `python -m app.worker`
6. Generate traffic:
   `python scripts/generate_logs.py --count 10000 --rate 200`
7. Open:
   `http://127.0.0.1:8000/docs`

## Benchmark
`python scripts/benchmark.py --count 100000`

The benchmark measures Kafka ingestion throughput. Do not claim 95% accuracy, 35% false-positive reduction, 60% response-time reduction, or 10,000+ events/minute on a resume until you have actually benchmarked/evaluated those numbers.

## API
POST /api/logs
GET /api/alerts
GET /api/incidents
PATCH /api/incidents/{id}
POST /api/incidents/{id}/respond
GET /api/metrics
GET /health
