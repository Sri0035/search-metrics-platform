"""Debug Kafka consumer for inspecting raw search events."""

import json
import os
import signal
import sys

from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_TOPIC = os.getenv("KAFKA_RAW_TOPIC", "raw-search-events")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "search-metrics-debug-consumer")

running = True


def shutdown(signum, frame):
    global running
    running = False
    print("\nShutting down consumer...")


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

    print(f"Listening on topic '{RAW_TOPIC}' ({BOOTSTRAP_SERVERS})")

    for message in consumer:
        if not running:
            break
        event = message.value
        print(
            f"[{message.partition}:{message.offset}] "
            f"{event['service_id']} | {event['status']} | "
            f"{event['latency_ms']}ms | {event['query'][:40]}"
        )

    consumer.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
