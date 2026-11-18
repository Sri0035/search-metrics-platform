"""Anomaly detection rules for search metrics pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class Anomaly:
    service_id: str
    anomaly_type: str
    detected_at: datetime
    severity: str
    metric_value: float
    threshold: float
    trace_id: Optional[str] = None


def load_sla_thresholds(database_url: str) -> dict[str, dict]:
    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT service_name, sla_latency_ms, sla_error_rate FROM service_registry"
            )
            rows = cur.fetchall()
    return {
        row["service_name"]: {
            "sla_latency_ms": row["sla_latency_ms"],
            "sla_error_rate": row["sla_error_rate"],
        }
        for row in rows
    }


def detect_anomalies(
    metrics_rows: list[dict],
    historical_rows: list[dict],
    sla_thresholds: dict[str, dict],
    hourly_baselines: dict[str, float],
) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    history_by_service: dict[str, list[float]] = {}

    for row in historical_rows:
        history_by_service.setdefault(row["service_id"], []).append(row["avg_latency"])

    for row in metrics_rows:
        service_id = row["service_id"]
        detected_at = row["window_end"]
        sla = sla_thresholds.get(service_id, {"sla_latency_ms": 300, "sla_error_rate": 0.05})

        latencies = history_by_service.get(service_id, [])
        if len(latencies) >= 3:
            mean = sum(latencies) / len(latencies)
            variance = sum((x - mean) ** 2 for x in latencies) / len(latencies)
            std = variance ** 0.5
            if std > 0:
                z_score = (row["avg_latency"] - mean) / std
                if z_score > 3:
                    anomalies.append(
                        Anomaly(
                            service_id=service_id,
                            anomaly_type="latency_spike",
                            detected_at=detected_at,
                            severity="HIGH",
                            metric_value=row["avg_latency"],
                            threshold=mean + 3 * std,
                        )
                    )

        if row["error_rate"] > sla["sla_error_rate"]:
            anomalies.append(
                Anomaly(
                    service_id=service_id,
                    anomaly_type="error_rate_surge",
                    detected_at=detected_at,
                    severity="CRITICAL",
                    metric_value=row["error_rate"],
                    threshold=sla["sla_error_rate"],
                    trace_id=row.get("sample_trace_id"),
                )
            )

        if row["avg_relevance"] < 0.5:
            anomalies.append(
                Anomaly(
                    service_id=service_id,
                    anomaly_type="relevance_drop",
                    detected_at=detected_at,
                    severity="MEDIUM",
                    metric_value=row["avg_relevance"],
                    threshold=0.5,
                )
            )

        baseline = hourly_baselines.get(service_id, 100)
        if baseline > 0 and row["query_count"] < baseline * 0.1:
            anomalies.append(
                Anomaly(
                    service_id=service_id,
                    anomaly_type="volume_anomaly",
                    detected_at=detected_at,
                    severity="LOW",
                    metric_value=float(row["query_count"]),
                    threshold=baseline * 0.1,
                )
            )

    return anomalies


def write_anomalies(database_url: str, anomalies: list[Anomaly]) -> None:
    if not anomalies:
        return

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            for anomaly in anomalies:
                cur.execute(
                    """
                    INSERT INTO anomaly_log
                        (service_id, anomaly_type, detected_at, severity,
                         metric_value, threshold, trace_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        anomaly.service_id,
                        anomaly.anomaly_type,
                        anomaly.detected_at,
                        anomaly.severity,
                        anomaly.metric_value,
                        anomaly.threshold,
                        anomaly.trace_id,
                    ),
                )
        conn.commit()
