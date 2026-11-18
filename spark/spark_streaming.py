"""PySpark structured streaming job: Kafka -> aggregates -> Postgres."""

import os
from datetime import datetime, timedelta

import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    expr,
    from_json,
    percentile_approx,
    sum as spark_sum,
    window,
)
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from anomaly_detector import detect_anomalies, load_sla_thresholds, write_anomalies

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_RAW_TOPIC = os.getenv("KAFKA_RAW_TOPIC", "raw-search-events")
KAFKA_ANOMALIES_TOPIC = os.getenv("KAFKA_ANOMALIES_TOPIC", "anomaly-alerts")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://searchmetrics:searchmetrics@postgres:5432/search_metrics",
)
CHECKPOINT_DIR = os.getenv("SPARK_CHECKPOINT_DIR", "/tmp/spark-checkpoints")

EVENT_SCHEMA = StructType(
    [
        StructField("trace_id", StringType(), False),
        StructField("query", StringType(), False),
        StructField("service_id", StringType(), False),
        StructField("latency_ms", IntegerType(), False),
        StructField("relevance_score", DoubleType(), False),
        StructField("status", StringType(), False),
        StructField("error_code", StringType(), True),
        StructField("timestamp", StringType(), False),
    ]
)


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("search-metrics-streaming")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def fetch_historical_metrics(database_url: str, service_id: str, minutes: int = 5) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT service_id, avg_latency, error_rate, query_count, avg_relevance, window_end
                FROM metrics_summary
                WHERE service_id = %s AND window_start >= %s
                ORDER BY window_start DESC
                LIMIT 20
                """,
                (service_id, cutoff),
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def fetch_hourly_baselines(database_url: str) -> dict[str, float]:
    cutoff = datetime.utcnow() - timedelta(hours=1)
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT service_id, AVG(query_count) AS baseline
                FROM metrics_summary
                WHERE window_start >= %s
                GROUP BY service_id
                """,
                (cutoff,),
            )
            return {row[0]: float(row[1] or 0) for row in cur.fetchall()}


def write_batch_to_postgres(batch_df, batch_id: int) -> None:
    if batch_df.rdd.isEmpty():
        return

    rows = batch_df.collect()
    sla_thresholds = load_sla_thresholds(DATABASE_URL)
    hourly_baselines = fetch_hourly_baselines(DATABASE_URL)

    metrics_rows = []
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for row in rows:
                metrics_row = {
                    "service_id": row["service_id"],
                    "window_start": row["window"]["start"],
                    "window_end": row["window"]["end"],
                    "avg_latency": float(row["avg_latency"]),
                    "p50_latency": float(row["p50_latency"]),
                    "p95_latency": float(row["p95_latency"]),
                    "p99_latency": float(row["p99_latency"]),
                    "error_rate": float(row["error_rate"]),
                    "query_count": int(row["query_count"]),
                    "avg_relevance": float(row["avg_relevance"]),
                }
                metrics_rows.append(metrics_row)

                cur.execute(
                    """
                    INSERT INTO metrics_summary
                        (service_id, window_start, window_end, avg_latency, p50_latency,
                         p95_latency, p99_latency, error_rate, query_count, avg_relevance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (service_id, window_start)
                    DO UPDATE SET
                        window_end = EXCLUDED.window_end,
                        avg_latency = EXCLUDED.avg_latency,
                        p50_latency = EXCLUDED.p50_latency,
                        p95_latency = EXCLUDED.p95_latency,
                        p99_latency = EXCLUDED.p99_latency,
                        error_rate = EXCLUDED.error_rate,
                        query_count = EXCLUDED.query_count,
                        avg_relevance = EXCLUDED.avg_relevance
                    """,
                    (
                        metrics_row["service_id"],
                        metrics_row["window_start"],
                        metrics_row["window_end"],
                        metrics_row["avg_latency"],
                        metrics_row["p50_latency"],
                        metrics_row["p95_latency"],
                        metrics_row["p99_latency"],
                        metrics_row["error_rate"],
                        metrics_row["query_count"],
                        metrics_row["avg_relevance"],
                    ),
                )
        conn.commit()

    all_historical = []
    for metrics_row in metrics_rows:
        historical = fetch_historical_metrics(DATABASE_URL, metrics_row["service_id"])
        all_historical.extend(historical)

    anomalies = detect_anomalies(
        metrics_rows, all_historical, sla_thresholds, hourly_baselines
    )
    write_anomalies(DATABASE_URL, anomalies)


def main() -> None:
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    raw_kafka = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_RAW_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = (
        raw_kafka.selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), EVENT_SCHEMA).alias("event"))
        .select("event.*")
        .withColumn("event_ts", col("timestamp").cast(TimestampType()))
    )

    aggregated = (
        parsed.withWatermark("event_ts", "2 minutes")
        .groupBy(window(col("event_ts"), "1 minute"), col("service_id"))
        .agg(
            count("*").alias("query_count"),
            avg("latency_ms").alias("avg_latency"),
            percentile_approx("latency_ms", 0.5).alias("p50_latency"),
            percentile_approx("latency_ms", 0.95).alias("p95_latency"),
            percentile_approx("latency_ms", 0.99).alias("p99_latency"),
            avg("relevance_score").alias("avg_relevance"),
            (
                spark_sum(expr("CASE WHEN status = 'error' THEN 1 ELSE 0 END")) / count("*")
            ).alias("error_rate"),
        )
    )

    query = (
        aggregated.writeStream.foreachBatch(write_batch_to_postgres)
        .outputMode("update")
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/metrics")
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
