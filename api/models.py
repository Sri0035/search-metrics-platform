from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(64), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    service_id = Column(String(100), nullable=False, index=True)
    latency_ms = Column(Integer, nullable=False)
    relevance_score = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    error_code = Column(String(50), nullable=True)
    ts = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_raw_events_service_ts", "service_id", "ts"),
    )


class MetricsSummary(Base):
    __tablename__ = "metrics_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String(100), nullable=False, index=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    avg_latency = Column(Float, nullable=False)
    p50_latency = Column(Float, nullable=True)
    p95_latency = Column(Float, nullable=False)
    p99_latency = Column(Float, nullable=False)
    error_rate = Column(Float, nullable=False)
    query_count = Column(Integer, nullable=False)
    avg_relevance = Column(Float, nullable=False)

    __table_args__ = (
        Index(
            "ix_metrics_summary_service_window",
            "service_id",
            "window_start",
            unique=True,
        ),
    )


class AnomalyLog(Base):
    __tablename__ = "anomaly_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String(100), nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    trace_id = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_anomaly_log_service_detected", "service_id", "detected_at"),
    )


class ServiceRegistry(Base):
    __tablename__ = "service_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(100), unique=True, nullable=False)
    owner_team = Column(String(100), nullable=False)
    sla_latency_ms = Column(Integer, nullable=False)
    sla_error_rate = Column(Float, nullable=False)


def get_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory(database_url: str):
    engine = get_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
