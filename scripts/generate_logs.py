import argparse, random, time, json
from datetime import datetime, timezone
from kafka import KafkaProducer
from app.config import KAFKA_BOOTSTRAP, LOG_TOPIC

def make_event(anomaly=False):
    return {
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "source_ip":f"10.0.0.{random.randint(1,254)}",
        "destination_ip":"10.0.0.10",
        "source_port":random.randint(1024,65535),
        "destination_port":random.choice([22,3389]) if anomaly else random.choice([53,80,443]),
        "protocol":"TCP",
        "event_type":"authentication" if anomaly else "network",
        "action":"failed_login" if anomaly else "connection",
        "username":"admin" if anomaly else None,
        "bytes_sent":random.randint(1500000,5000000) if anomaly else random.randint(100,50000),
        "bytes_received":random.randint(100,10000),
        "duration_ms":random.randint(5000,30000) if anomaly else random.uniform(1,250),
        "failed_attempts":random.randint(8,30) if anomaly else random.choice([0,0,0,1])}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--count",type=int,default=10000)
    ap.add_argument("--rate",type=int,default=200)
    ap.add_argument("--anomaly-rate",type=float,default=0.05)
    args=ap.parse_args()
    p=KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v:json.dumps(v).encode(),
        linger_ms=5,batch_size=32768,compression_type="lz4")
    start=time.perf_counter(); interval=1/max(args.rate,1)
    for i in range(args.count):
        p.send(LOG_TOPIC,make_event(random.random()<args.anomaly_rate))
        if i%1000==0: p.flush()
        time.sleep(interval)
    p.flush(); elapsed=time.perf_counter()-start
    print(f"Sent {args.count:,} events in {elapsed:.2f}s")
    print(f"Producer throughput: {args.count/elapsed:,.0f} events/sec")

if __name__=="__main__": main()
