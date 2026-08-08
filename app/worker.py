import logging
import uuid
from .config import LOG_TOPIC, ALERT_TOPIC, ANOMALY_THRESHOLD
from .kafka_client import consumer, producer
from .ml_detector import AnomalyDetector
from .db import init_db, save_alert, create_incident

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("soc-worker")

def severity(score, event):
    if event.get("failed_attempts",0) >= 10 or score < -0.20: return "critical"
    if score < -0.12: return "high"
    if score < ANOMALY_THRESHOLD: return "medium"
    return "low"

def reason(event):
    reasons=[]
    if event.get("failed_attempts",0) >= 5:
        reasons.append("repeated authentication failures")
    if event.get("bytes_sent",0) > 1000000:
        reasons.append("unusually high outbound traffic")
    if event.get("destination_port") in {22,3389} and event.get("failed_attempts",0) >= 3:
        reasons.append("suspicious remote-access activity")
    return ", ".join(reasons) or "ML anomaly detected"

def main():
    init_db(); detector=AnomalyDetector()
    c=consumer(LOG_TOPIC,"soc-detection-worker"); p=producer()
    logger.info("Detection worker started")
    for msg in c:
        event=msg.value
        anomaly,score=detector.is_anomaly(event)
        if not anomaly: continue
        alert={
            "alert_id":str(uuid.uuid4()), "timestamp":event.get("timestamp"),
            "source_ip":event.get("source_ip"), "anomaly_score":score,
            "severity":severity(score,event), "reason":reason(event),
            "event":event, "status":"open"}
        save_alert(alert); create_incident(alert["alert_id"])
        p.send(ALERT_TOPIC,alert)
        logger.info("Alert %s | %s | score=%.4f",
                    alert["alert_id"],alert["severity"],score)

if __name__ == "__main__":
    main()
