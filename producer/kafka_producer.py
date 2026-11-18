"""Synthetic search traffic generator for the metrics platform."""

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_TOPIC = os.getenv("KAFKA_RAW_TOPIC", "raw-search-events")
EVENTS_PER_MINUTE = int(os.getenv("EVENTS_PER_MINUTE", "1000"))
SERVICE_IDS = os.getenv("SERVICE_IDS", "search-api,recommendations,indexer,ranking").split(",")

SAMPLE_QUERIES = [
    "wireless headphones",
    "python tutorial",
    "best pizza near me",
    "machine learning courses",
    "weather today",
    "react dashboard components",
    "kafka streaming example",
    "postgresql indexing",
    "running shoes sale",
    "cloud architecture patterns",
]

ERROR_CODES = ["TIMEOUT", "404", "500", None, None, None, None]


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )


def generate_event(service_id: str) -> dict:
    is_error = random.random() < 0.03
    base_latency = {
        "search-api": 120,
        "recommendations": 280,
        "indexer": 400,
        "ranking": 180,
    }.get(service_id, 200)

    latency = max(10, int(random.gauss(base_latency, base_latency * 0.3)))
    if is_error:
        latency = int(latency * random.uniform(1.5, 3.0))

    if random.random() < 0.005:
        latency = int(base_latency * random.uniform(4, 8))

    relevance = round(random.uniform(0.4, 0.98), 2)
    if random.random() < 0.02:
        relevance = round(random.uniform(0.1, 0.45), 2)

    return {
        "trace_id": str(uuid.uuid4()),
        "query": random.choice(SAMPLE_QUERIES),
        "service_id": service_id,
        "latency_ms": latency,
        "relevance_score": relevance,
        "status": "error" if is_error else "success",
        "error_code": random.choice(ERROR_CODES) if is_error else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    producer = create_producer()
    interval = 60.0 / max(EVENTS_PER_MINUTE, 1)
    print(
        f"Producing ~{EVENTS_PER_MINUTE} events/min to '{RAW_TOPIC}' "
        f"via {BOOTSTRAP_SERVERS}"
    )

    while True:
        service_id = random.choice(SERVICE_IDS)
        event = generate_event(service_id)
        producer.send(RAW_TOPIC, value=event, key=event["service_id"].encode())
        time.sleep(interval)


if __name__ == "__main__":
    main()
