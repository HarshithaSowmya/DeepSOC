"""Benchmarks the actual detection pipeline throughput: event generation +
feature scoring + (for anomalies) DB write, i.e. what the system can really
process per minute end-to-end. This is different from scripts/benchmark.py,
which only measures how fast the Kafka producer can hand off messages
(network I/O), not how fast events are actually scored and turned into
alerts/incidents.
"""
import argparse
import time
from app.ml_detector import AnomalyDetector
from app.db import init_db
from app.detection import process_event
from app.simulator import make_event
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20000)
    ap.add_argument("--anomaly-rate", type=float, default=0.10)
    ap.add_argument("--persist", action="store_true",
                     help="Actually write alerts/incidents to soc.db (slower, realistic). "
                          "Without this flag, only the ML scoring step is timed.")
    args = ap.parse_args()

    detector = AnomalyDetector()
    if args.persist:
        init_db()

    events = [make_event(anomaly=random.random() < args.anomaly_rate) for _ in range(args.count)]

    start = time.perf_counter()
    alerts = 0
    for event in events:
        if args.persist:
            if process_event(detector, event):
                alerts += 1
        else:
            anomaly, _ = detector.is_anomaly(event)
            alerts += int(anomaly)
    elapsed = time.perf_counter() - start

    print("=== SOC Pipeline Throughput Benchmark ===")
    print(f"Mode: {'scoring + DB persistence' if args.persist else 'ML scoring only'}")
    print(f"Events processed: {args.count:,}")
    print(f"Alerts generated: {alerts:,}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Throughput: {args.count/elapsed:,.0f} events/sec")
    print(f"Throughput: {(args.count/elapsed)*60:,.0f} events/min")


if __name__ == "__main__":
    main()
