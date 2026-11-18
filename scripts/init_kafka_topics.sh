#!/bin/bash
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-kafka:29092}"

echo "Creating Kafka topics on ${BOOTSTRAP}..."

kafka-topics --bootstrap-server "${BOOTSTRAP}" --create --if-not-exists \
  --topic raw-search-events --partitions 8 --replication-factor 1 \
  --config retention.ms=86400000

kafka-topics --bootstrap-server "${BOOTSTRAP}" --create --if-not-exists \
  --topic processed-metrics --partitions 4 --replication-factor 1 \
  --config retention.ms=21600000

kafka-topics --bootstrap-server "${BOOTSTRAP}" --create --if-not-exists \
  --topic anomaly-alerts --partitions 2 --replication-factor 1 \
  --config retention.ms=172800000

kafka-topics --bootstrap-server "${BOOTSTRAP}" --list
echo "Kafka topics ready."
