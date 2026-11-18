from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import AnomalyLog, MetricsSummary, RawEvent, ServiceRegistry
from api.schemas import (
    AnomalyResponse,
    MetricsSummaryResponse,
    ServiceResponse,
    SummaryAggregateResponse,
    TraceEventResponse,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=SummaryAggregateResponse)
def get_metrics_summary(
    minutes: int = Query(default=60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)
    rows = (
        db.query(MetricsSummary)
        .filter(MetricsSummary.window_start >= cutoff)
        .order_by(MetricsSummary.window_start.desc())
        .all()
    )

    services = [
        MetricsSummaryResponse(
            service_id=row.service_id,
            window_start=row.window_start,
            window_end=row.window_end,
            avg_latency=row.avg_latency,
            p50_latency=row.p50_latency,
            p95_latency=row.p95_latency,
            p99_latency=row.p99_latency,
            error_rate=row.error_rate,
            query_count=row.query_count,
            avg_relevance=row.avg_relevance,
        )
        for row in rows
    ]

    total_query_count = sum(s.query_count for s in services)
    avg_error_rate = (
        sum(s.error_rate for s in services) / len(services) if services else 0.0
    )

    return SummaryAggregateResponse(
        services=services,
        total_query_count=total_query_count,
        avg_error_rate=avg_error_rate,
    )


@router.get("/service/{service_id}", response_model=list[MetricsSummaryResponse])
def get_service_metrics(
    service_id: str,
    minutes: int = Query(default=60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)
    rows = (
        db.query(MetricsSummary)
        .filter(
            MetricsSummary.service_id == service_id,
            MetricsSummary.window_start >= cutoff,
        )
        .order_by(MetricsSummary.window_start.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail=f"No metrics for service '{service_id}'")

    return [
        MetricsSummaryResponse(
            service_id=row.service_id,
            window_start=row.window_start,
            window_end=row.window_end,
            avg_latency=row.avg_latency,
            p50_latency=row.p50_latency,
            p95_latency=row.p95_latency,
            p99_latency=row.p99_latency,
            error_rate=row.error_rate,
            query_count=row.query_count,
            avg_relevance=row.avg_relevance,
        )
        for row in rows
    ]
