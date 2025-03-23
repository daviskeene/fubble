from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fubble.database.connection import get_db
from fubble.core.usage import UsageManager


router = APIRouter(prefix="/usage", tags=["usage"])


class UsageEventCreate(BaseModel):
    customer_id: int
    metric_name: str
    quantity: float = Field(..., gt=0)
    subscription_id: Optional[int] = None
    event_time: Optional[str] = None  # ISO format date
    properties: Optional[Dict[str, Any]] = None
    billing_period_id: Optional[int] = None


class UsageEventResponse(BaseModel):
    id: int
    customer_id: int
    subscription_id: int
    metric_name: str
    quantity: float
    event_time: str
    properties: Optional[Dict[str, Any]] = None
    billing_period_id: Optional[int] = None
    created_at: str

    class Config:
        orm_mode = True


class UsageQueryParams(BaseModel):
    start_date: str
    end_date: str
    metric_name: Optional[str] = None


@router.post(
    "/track", response_model=UsageEventResponse, status_code=status.HTTP_201_CREATED
)
def track_usage(usage_data: UsageEventCreate, db: Session = Depends(get_db)):
    """Record a usage event for a customer."""
    usage_manager = UsageManager(db)

    # Parse the event time if provided
    event_time = None
    if usage_data.event_time:
        try:
            event_time = datetime.fromisoformat(usage_data.event_time)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    try:
        # Record the usage event
        usage_event = usage_manager.record_usage(
            customer_id=usage_data.customer_id,
            metric_name=usage_data.metric_name,
            quantity=usage_data.quantity,
            subscription_id=usage_data.subscription_id,
            event_time=event_time,
            properties=usage_data.properties,
            billing_period_id=usage_data.billing_period_id,
        )

        return usage_event

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/customer/{customer_id}", response_model=Dict[str, float])
def get_customer_usage(
    customer_id: int,
    start_date: str,
    end_date: str,
    metric_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get usage for a customer during a specific period."""
    usage_manager = UsageManager(db)

    # Parse dates
    try:
        parsed_start_date = datetime.fromisoformat(start_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
        )

    try:
        parsed_end_date = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
        )

    # Get the usage
    usage = usage_manager.get_usage_for_period(
        customer_id=customer_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        metric_name=metric_name,
    )

    return usage
