from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import AnomalyLog
from api.schemas import AnomalyResponse

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyResponse])
def list_anomalies(
    hours: int = Query(default=24, ge=1, le=168),
    severity: str | None = Query(default=None),
    service_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    query = db.query(AnomalyLog).filter(AnomalyLog.detected_at >= cutoff)

    if severity:
        query = query.filter(AnomalyLog.severity == severity.upper())
    if service_id:
        query = query.filter(AnomalyLog.service_id == service_id)

    rows = query.order_by(desc(AnomalyLog.detected_at)).limit(100).all()

    return [
        AnomalyResponse(
            id=row.id,
            service_id=row.service_id,
            anomaly_type=row.anomaly_type,
            detected_at=row.detected_at,
            severity=row.severity,
            metric_value=row.metric_value,
            threshold=row.threshold,
            trace_id=row.trace_id,
        )
        for row in rows
    ]
