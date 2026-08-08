import argparse,json,random,time
from datetime import datetime,timezone
from kafka import KafkaProducer
from app.config import KAFKA_BOOTSTRAP,LOG_TOPIC

def event(i):
    anomaly=i%20==0
    return {
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "source_ip":f"10.0.0.{(i%254)+1}","destination_ip":"10.0.0.10",
        "source_port":random.randint(1024,65535),
        "destination_port":22 if anomaly else 443,
        "protocol":"TCP","event_type":"authentication" if anomaly else "network",
        "action":"failed_login" if anomaly else "connection",
        "username":"admin" if anomaly else None,
        "bytes_sent":random.randint(2000000,5000000) if anomaly else random.randint(100,50000),
        "bytes_received":random.randint(100,10000),
        "duration_ms":random.randint(5000,30000) if anomaly else random.uniform(1,250),
        "failed_attempts":random.randint(8,20) if anomaly else 0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--count",type=int,default=100000)
    args=ap.parse_args()
    p=KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v:json.dumps(v).encode(),
        linger_ms=5,batch_size=65536,compression_type="lz4",acks=1)
    start=time.perf_counter()
    for i in range(args.count): p.send(LOG_TOPIC,event(i))
    p.flush(); elapsed=time.perf_counter()-start
    print("=== SOC Ingestion Benchmark ===")
    print(f"Events: {args.count:,}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Throughput: {args.count/elapsed:,.0f} events/sec")
    print(f"Throughput: {(args.count/elapsed)*60:,.0f} events/min")
    print("Note: this measures Kafka producer throughput, not model accuracy.")

if __name__=="__main__": main()
