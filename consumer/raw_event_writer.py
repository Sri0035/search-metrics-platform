"""Kafka consumer that persists raw search events to PostgreSQL."""

import json
import os
import signal
import sys
from datetime import datetime

import psycopg2
from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
RAW_TOPIC = os.getenv("KAFKA_RAW_TOPIC", "raw-search-events")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "search-metrics-raw-writer")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://searchmetrics:searchmetrics@postgres:5432/search_metrics",
)

running = True


def shutdown(signum, frame):
    global running
    running = False


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def write_event(conn, event: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_events
                (trace_id, query_text, service_id, latency_ms,
                 relevance_score, status, error_code, ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event["trace_id"],
                event["query"],
                event["service_id"],
                event["latency_ms"],
                event["relevance_score"],
                event["status"],
                event.get("error_code"),
                parse_timestamp(event["timestamp"]),
            ),
        )


def main() -> None:
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    consumer = KafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    conn = psycopg2.connect(DATABASE_URL)
    print(f"Writing raw events from '{RAW_TOPIC}' to Postgres")

    try:
        for message in consumer:
            if not running:
                break
            write_event(conn, message.value)
            conn.commit()
    finally:
        conn.close()
        consumer.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
