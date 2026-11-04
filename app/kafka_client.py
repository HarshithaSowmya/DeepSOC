import json
import socket
from kafka import KafkaProducer, KafkaConsumer
from .config import KAFKA_BOOTSTRAP, KAFKA_CONNECT_TIMEOUT


def kafka_reachable():
    """Quick TCP check so we can decide Kafka vs. in-process demo mode
    at startup without waiting on the much slower kafka-python client
    timeout/retry logic."""
    host, _, port = KAFKA_BOOTSTRAP.partition(":")
    port = int(port) if port else 9092
    try:
        with socket.create_connection((host, port), timeout=KAFKA_CONNECT_TIMEOUT):
            return True
    except OSError:
        return False

def producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        linger_ms=5, batch_size=32768,
        compression_type="gzip", acks="all")

def consumer(topic, group_id):
    return KafkaConsumer(
        topic, bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=group_id, auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode()),
        max_poll_records=500)
