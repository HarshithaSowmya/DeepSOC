"""Real evaluation of the anomaly detector against labeled synthetic data.

Ground truth is known because we control the generator: each event is
tagged 'is_attack' when we generated it, and the detector's prediction is
compared against that label. This is what should back any accuracy /
false-positive claim about the project -- not an assumed number.

Usage:
    python -m scripts.evaluate_accuracy --count 5000 --attack-rate 0.10
"""
import argparse
import random
from datetime import datetime, timezone
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
)
from app.ml_detector import AnomalyDetector


def make_labeled_event(is_attack):
    return {
        "is_attack": is_attack,
        "event": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": f"10.0.0.{random.randint(1, 254)}",
            "destination_ip": "10.0.0.10",
            "source_port": random.randint(1024, 65535),
            "destination_port": random.choice([22, 3389]) if is_attack else random.choice([53, 80, 443]),
            "protocol": "TCP",
            "event_type": "authentication" if is_attack else "network",
            "action": "failed_login" if is_attack else "connection",
            "username": "admin" if is_attack else None,
            "bytes_sent": random.randint(1_500_000, 5_000_000) if is_attack else random.randint(100, 50000),
            "bytes_received": random.randint(100, 10000),
            "duration_ms": random.randint(5000, 30000) if is_attack else round(random.uniform(1, 250), 2),
            "failed_attempts": random.randint(8, 30) if is_attack else random.choice([0, 0, 0, 1]),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5000)
    ap.add_argument("--attack-rate", type=float, default=0.10)
    args = ap.parse_args()

    detector = AnomalyDetector()
    y_true, y_pred = [], []
    for _ in range(args.count):
        is_attack = random.random() < args.attack_rate
        row = make_labeled_event(is_attack)
        predicted_anomaly, score = detector.is_anomaly(row["event"])
        y_true.append(int(row["is_attack"]))
        y_pred.append(int(predicted_anomaly))

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    print("=== Detector Evaluation (labeled synthetic data) ===")
    print(f"Samples: {args.count:,}  (attack rate: {args.attack_rate:.0%})")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"False Positive Rate: {fpr:.4f}")
    print(f"Confusion matrix -> TN={tn} FP={fp} FN={fn} TP={tp}")
    print()
    print("NOTE: this measures the model against synthetic traffic generated")
    print("from the same distribution the detector was trained/normalized on.")
    print("It demonstrates the detector works as designed -- it is NOT a claim")
    print("about performance against real-world attack traffic, which would")
    print("need a labeled real (or public) intrusion-detection dataset.")


if __name__ == "__main__":
    main()
