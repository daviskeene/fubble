from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, root_validator

from fubble.database.connection import get_db
from fubble.core.events import EventTracker
from fubble.database.models import UsageEvent


router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    customer_id: int
    metric_name: str = Field(..., min_length=1, max_length=255)
    quantity: float = Field(..., gt=0)
    event_time: Optional[str] = None  # ISO format date
    properties: Optional[Dict[str, Any]] = None


class BatchEventCreate(BaseModel):
    events: List[EventCreate]


class EventResponse(BaseModel):
    id: int
    customer_id: int
    billing_period_id: Optional[int]
    metric_name: str
    quantity: float
    event_time: str  # ISO format date
    properties: Optional[Dict[str, Any]]
    created_at: str  # ISO format date

    class Config:
        orm_mode = True  # For Pydantic v1

    @root_validator(pre=True)
    def convert_datetime_to_str(cls, values):
        # Handle both dictionary and model objects
        if not isinstance(values, dict):
            # If values is an ORM model like UsageEvent, convert it to a dict first
            if hasattr(values, "__dict__"):
                # For ORM models that have __dict__
                values_dict = {}
                for field in [
                    "id",
                    "customer_id",
                    "billing_period_id",
                    "metric_name",
                    "quantity",
                    "event_time",
                    "properties",
                    "created_at",
                ]:
                    if hasattr(values, field):
                        values_dict[field] = getattr(values, field)
                values = values_dict

        # Now process the dictionary
        if isinstance(values, dict):
            # Convert datetime to string for certain fields
            for field in ["event_time", "created_at"]:
                if field in values and isinstance(values[field], datetime):
                    values[field] = values[field].isoformat()

        return values


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def track_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Track a new usage event."""
    event_tracker = EventTracker(db)

    # Parse event time if provided
    event_time = None
    if event_data.event_time:
        try:
            event_time = datetime.fromisoformat(event_data.event_time)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    # Create the event
    event = event_tracker.track_event(
        customer_id=event_data.customer_id,
        metric_name=event_data.metric_name,
        quantity=event_data.quantity,
        event_time=event_time,
        properties=event_data.properties,
    )

    # Convert datetime fields to strings manually
    event_dict = {
        "id": event.id,
        "customer_id": event.customer_id,
        "billing_period_id": event.billing_period_id,
        "metric_name": event.metric_name,
        "quantity": event.quantity,
        "event_time": event.event_time.isoformat() if event.event_time else None,
        "properties": event.properties,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }

    return event_dict


@router.post(
    "/batch", response_model=List[EventResponse], status_code=status.HTTP_201_CREATED
)
def batch_track_events(batch_data: BatchEventCreate, db: Session = Depends(get_db)):
    """Track multiple usage events in a batch."""
    event_tracker = EventTracker(db)

    # Prepare event data for batch processing
    events_data = []
    for event_data in batch_data.events:
        # Parse event time if provided
        event_time = None
        if event_data.event_time:
            try:
                event_time = datetime.fromisoformat(event_data.event_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event_time format for event with metric {event_data.metric_name}. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
                )

        events_data.append(
            {
                "customer_id": event_data.customer_id,
                "metric_name": event_data.metric_name,
                "quantity": event_data.quantity,
                "event_time": event_time,
                "properties": event_data.properties,
            }
        )

    # Create the events in batch
    events = event_tracker.batch_track_events(events_data)

    return events


@router.get("/customers/{customer_id}", response_model=List[EventResponse])
def get_customer_events(
    customer_id: int,
    start_date: str,
    end_date: str,
    metric_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get usage events for a customer in a date range."""
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

    # Query events
    query = db.query(UsageEvent).filter(
        UsageEvent.customer_id == customer_id,
        UsageEvent.event_time >= parsed_start_date,
        UsageEvent.event_time <= parsed_end_date,
    )

    if metric_name:
        query = query.filter(UsageEvent.metric_name == metric_name)

    events = query.order_by(UsageEvent.event_time.desc()).all()

    return events


@router.get("/customers/{customer_id}/usage", response_model=Dict[str, float])
def get_customer_usage(
    customer_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)
):
    """Get aggregated usage by metric for a customer in a date range."""
    event_tracker = EventTracker(db)

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

    # Get usage data
    usage_data = event_tracker.get_usage_by_metric(
        customer_id=customer_id, start_date=parsed_start_date, end_date=parsed_end_date
    )

    return usage_data
