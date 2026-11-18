from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetricsSummaryResponse(BaseModel):
    service_id: str
    window_start: datetime
    window_end: datetime
    avg_latency: float
    p50_latency: Optional[float] = None
    p95_latency: float
    p99_latency: float
    error_rate: float
    query_count: int
    avg_relevance: float


class AnomalyResponse(BaseModel):
    id: int
    service_id: str
    anomaly_type: str
    detected_at: datetime
    severity: str
    metric_value: float
    threshold: float
    trace_id: Optional[str] = None


class TraceEventResponse(BaseModel):
    trace_id: str
    query_text: str
    service_id: str
    latency_ms: int
    relevance_score: float
    status: str
    error_code: Optional[str] = None
    ts: datetime


class ServiceResponse(BaseModel):
    id: int
    service_name: str
    owner_team: str
    sla_latency_ms: int
    sla_error_rate: float


class SummaryAggregateResponse(BaseModel):
    services: list[MetricsSummaryResponse]
    total_query_count: int = Field(default=0)
    avg_error_rate: float = Field(default=0.0)
