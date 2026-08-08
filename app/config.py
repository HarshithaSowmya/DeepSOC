import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
LOG_TOPIC = os.getenv("LOG_TOPIC", "security-logs")
ALERT_TOPIC = os.getenv("ALERT_TOPIC", "security-alerts")
DB_PATH = os.getenv("DB_PATH", "soc.db")
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "-0.05"))
