import json
from kafka import KafkaProducer, KafkaConsumer
from .config import KAFKA_BOOTSTRAP

def producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        linger_ms=5, batch_size=32768,
        compression_type="lz4", acks=1)

def consumer(topic, group_id):
    return KafkaConsumer(
        topic, bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=group_id, auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode()),
        max_poll_records=500)
