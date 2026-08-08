from app.ml_detector import AnomalyDetector

def test_detector_returns_score():
    d=AnomalyDetector()
    event={"source_port":50000,"destination_port":443,"bytes_sent":500,
           "bytes_received":1000,"duration_ms":50,"failed_attempts":0}
    anomaly,score=d.is_anomaly(event)
    assert isinstance(anomaly,bool)
    assert isinstance(score,float)
