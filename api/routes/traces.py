from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import RawEvent
from api.schemas import TraceEventResponse

router = APIRouter(prefix="/trace", tags=["traces"])


@router.get("/{trace_id}", response_model=list[TraceEventResponse])
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(RawEvent)
        .filter(RawEvent.trace_id == trace_id)
        .order_by(RawEvent.ts.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")

    return [
        TraceEventResponse(
            trace_id=row.trace_id,
            query_text=row.query_text,
            service_id=row.service_id,
            latency_ms=row.latency_ms,
            relevance_score=row.relevance_score,
            status=row.status,
            error_code=row.error_code,
            ts=row.ts,
        )
        for row in rows
    ]
