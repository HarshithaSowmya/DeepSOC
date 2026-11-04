import logging
from .config import LOG_TOPIC
from .kafka_client import consumer
from .ml_detector import AnomalyDetector
from .db import init_db
from .detection import process_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("soc-worker")


def main():
    init_db()
    detector = AnomalyDetector()
    c = consumer(LOG_TOPIC, "soc-detection-worker")
    logger.info("Detection worker started (Kafka mode)")
    for msg in c:
        event = msg.value
        alert = process_event(detector, event)
        c.commit()
        if alert:
            logger.info("Alert %s | %s | score=%.4f",
                        alert["alert_id"], alert["severity"], alert["anomaly_score"])


if __name__ == "__main__":
    main()
