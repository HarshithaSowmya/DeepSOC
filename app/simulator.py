"""In-process traffic generator used when no Kafka broker is reachable
(e.g. a single-dyno Render deployment). Feeds synthetic events through the
exact same AnomalyDetector + detection.process_event() path that the real
Kafka worker uses, so alerts/incidents shown on the dashboard are genuinely
produced by the ML model rather than hardcoded.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone
from .config import DEMO_EVENTS_PER_SEC, DEMO_ANOMALY_RATE
from .detection import process_event

logger = logging.getLogger("soc-simulator")


def make_event(anomaly=False):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": f"10.0.0.{random.randint(1, 254)}",
        "destination_ip": "10.0.0.10",
        "source_port": random.randint(1024, 65535),
        "destination_port": random.choice([22, 3389]) if anomaly else random.choice([53, 80, 443]),
        "protocol": "TCP",
        "event_type": "authentication" if anomaly else "network",
        "action": "failed_login" if anomaly else "connection",
        "username": "admin" if anomaly else None,
        "bytes_sent": random.randint(1_500_000, 5_000_000) if anomaly else random.randint(100, 50000),
        "bytes_received": random.randint(100, 10000),
        "duration_ms": random.randint(5000, 30000) if anomaly else round(random.uniform(1, 250), 2),
        "failed_attempts": random.randint(8, 30) if anomaly else random.choice([0, 0, 0, 1]),
    }


async def run(detector, stop_event: asyncio.Event, on_event=None):
    """Continuously generate events and run them through the detector
    until stop_event is set. Runs as a background asyncio task.

    on_event: optional callback invoked once per generated event, used to
    keep the /api/metrics counters accurate.
    """
    delay = 1.0 / max(DEMO_EVENTS_PER_SEC, 0.1)
    logger.info(
        "Demo traffic simulator started (~%.1f events/sec, %.0f%% anomaly rate)",
        DEMO_EVENTS_PER_SEC, DEMO_ANOMALY_RATE * 100,
    )
    events_seen = 0
    while not stop_event.is_set():
        event = make_event(anomaly=random.random() < DEMO_ANOMALY_RATE)
        alert = await asyncio.to_thread(process_event, detector, event)
        events_seen += 1
        if on_event:
            on_event(alert)
        if alert:
            logger.info(
                "Alert %s | %s | score=%.4f",
                alert["alert_id"], alert["severity"], alert["anomaly_score"],
            )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass
    logger.info("Demo traffic simulator stopped after %d events", events_seen)
