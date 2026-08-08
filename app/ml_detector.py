import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["source_port","destination_port","bytes_sent",
            "bytes_received","duration_ms","failed_attempts"]

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=120, contamination=0.05,
            random_state=42, n_jobs=-1)
        rng = np.random.default_rng(42)
        normal = np.column_stack([
            rng.integers(1024, 60000, 5000),
            rng.choice([53,80,443,22,3389], 5000),
            rng.lognormal(7, 0.7, 5000),
            rng.lognormal(7.5, 0.7, 5000),
            rng.gamma(2, 25, 5000),
            rng.poisson(0.2, 5000)])
        self.model.fit(normal)

    def score(self, event):
        x = np.array([[event.get(k, 0) for k in FEATURES]], dtype=float)
        return float(self.model.decision_function(x)[0])

    def is_anomaly(self, event):
        score = self.score(event)
        return score < -0.05, score
