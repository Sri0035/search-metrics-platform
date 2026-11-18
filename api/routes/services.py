from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import ServiceRegistry
from api.schemas import ServiceResponse

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceResponse])
def list_services(db: Session = Depends(get_db)):
    rows = db.query(ServiceRegistry).order_by(ServiceRegistry.service_name).all()
    return [
        ServiceResponse(
            id=row.id,
            service_name=row.service_name,
            owner_team=row.owner_team,
            sla_latency_ms=row.sla_latency_ms,
            sla_error_rate=row.sla_error_rate,
        )
        for row in rows
    ]
