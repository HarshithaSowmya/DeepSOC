import numpy as np
from sklearn.ensemble import IsolationForest
from .config import ANOMALY_THRESHOLD

FEATURES = ["source_port","destination_port","bytes_sent",
            "bytes_received","duration_ms","failed_attempts"]

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=120, contamination=0.05,
            random_state=42, n_jobs=-1)
        rng = np.random.default_rng(42)
        n = 8000
        # "Normal" training data is generated from the SAME distribution
        # the app's own traffic generator (app/simulator.py) uses to
        # produce benign events -- not an arbitrary distribution that
        # happens to look plausible. Training on a mismatched distribution
        # made ordinary traffic look anomalous to the model regardless of
        # threshold tuning.
        dest_ports = rng.choice([53, 80, 443], n, p=[0.30, 0.40, 0.30])
        normal = np.column_stack([
            rng.integers(1024, 65535, n),
            dest_ports,
            rng.integers(100, 50000, n),
            rng.integers(100, 10000, n),
            rng.uniform(1, 250, n),
            rng.choice([0, 0, 0, 1], n)])
        self.model.fit(normal)

    def score(self, event):
        x = np.array([[event.get(k, 0) for k in FEATURES]], dtype=float)
        return float(self.model.decision_function(x)[0])

    def is_anomaly(self, event):
        score = self.score(event)
        return score < ANOMALY_THRESHOLD, score
