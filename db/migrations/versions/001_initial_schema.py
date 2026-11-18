"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("owner_team", sa.String(length=100), nullable=False),
        sa.Column("sla_latency_ms", sa.Integer(), nullable=False),
        sa.Column("sla_error_rate", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_name"),
    )

    op.create_table(
        "raw_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_events_trace_id", "raw_events", ["trace_id"])
    op.create_index("ix_raw_events_service_id", "raw_events", ["service_id"])
    op.create_index("ix_raw_events_ts", "raw_events", ["ts"])
    op.create_index("ix_raw_events_service_ts", "raw_events", ["service_id", "ts"])

    op.create_table(
        "metrics_summary",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("avg_latency", sa.Float(), nullable=False),
        sa.Column("p50_latency", sa.Float(), nullable=True),
        sa.Column("p95_latency", sa.Float(), nullable=False),
        sa.Column("p99_latency", sa.Float(), nullable=False),
        sa.Column("error_rate", sa.Float(), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False),
        sa.Column("avg_relevance", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metrics_summary_service_id", "metrics_summary", ["service_id"])
    op.create_index(
        "ix_metrics_summary_service_window",
        "metrics_summary",
        ["service_id", "window_start"],
        unique=True,
    )

    op.create_table(
        "anomaly_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_id", sa.String(length=100), nullable=False),
        sa.Column("anomaly_type", sa.String(length=50), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anomaly_log_service_id", "anomaly_log", ["service_id"])
    op.create_index("ix_anomaly_log_detected_at", "anomaly_log", ["detected_at"])
    op.create_index(
        "ix_anomaly_log_service_detected",
        "anomaly_log",
        ["service_id", "detected_at"],
    )

    op.execute(
        """
        INSERT INTO service_registry (service_name, owner_team, sla_latency_ms, sla_error_rate)
        VALUES
            ('search-api', 'Search Platform', 200, 0.02),
            ('recommendations', 'ML Team', 350, 0.03),
            ('indexer', 'Data Infra', 500, 0.01),
            ('ranking', 'Search Platform', 250, 0.025)
        ON CONFLICT (service_name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("anomaly_log")
    op.drop_table("metrics_summary")
    op.drop_table("raw_events")
    op.drop_table("service_registry")
