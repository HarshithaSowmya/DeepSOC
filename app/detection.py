"""Shared detection logic used by both the Kafka worker (app/worker.py)
and the in-process demo pipeline (app/simulator.py) so severity/reason
rules live in exactly one place.
"""
import uuid
from .config import ANOMALY_THRESHOLD
from .db import persist_detection


def severity(score, event):
    if event.get("failed_attempts", 0) >= 10 or score < -0.20:
        return "critical"
    if score < -0.12:
        return "high"
    if score < ANOMALY_THRESHOLD:
        return "medium"
    return "low"


def reason(event):
    reasons = []
    if event.get("failed_attempts", 0) >= 5:
        reasons.append("repeated authentication failures")
    if event.get("bytes_sent", 0) > 1000000:
        reasons.append("unusually high outbound traffic")
    if event.get("destination_port") in {22, 3389} and event.get("failed_attempts", 0) >= 3:
        reasons.append("suspicious remote-access activity")
    return ", ".join(reasons) or "ML anomaly detected"


def build_alert(event, score):
    return {
        "alert_id": str(uuid.uuid4()),
        "timestamp": event.get("timestamp"),
        "source_ip": event.get("source_ip"),
        "anomaly_score": score,
        "severity": severity(score, event),
        "reason": reason(event),
        "event": event,
        "status": "open",
    }


def process_event(detector, event):
    """Score one event and, if anomalous, persist an alert + incident.

    Returns the alert dict if one was created, otherwise None.
    """
    anomaly, score = detector.is_anomaly(event)
    alert = build_alert(event, score) if anomaly else None
    persist_detection(alert)
    return alert
