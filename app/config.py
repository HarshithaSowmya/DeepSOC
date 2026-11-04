import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
LOG_TOPIC = os.getenv("LOG_TOPIC", "security-logs")
ALERT_TOPIC = os.getenv("ALERT_TOPIC", "security-alerts")
DB_PATH = os.getenv("DB_PATH", "soc.db")
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.0"))

# How long to wait for Kafka before falling back to in-process demo mode.
KAFKA_CONNECT_TIMEOUT = float(os.getenv("KAFKA_CONNECT_TIMEOUT", "2.0"))

# Force a specific mode instead of auto-detecting Kafka reachability.
# "auto" (default) | "kafka" | "demo"
SOC_MODE = os.getenv("SOC_MODE", "auto")

# Synthetic traffic rate for in-process demo mode (events/second).
DEMO_EVENTS_PER_SEC = float(os.getenv("DEMO_EVENTS_PER_SEC", "2.0"))
DEMO_ANOMALY_RATE = float(os.getenv("DEMO_ANOMALY_RATE", "0.10"))
