from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, root_validator
import logging

from fubble.database.connection import get_db
from fubble.core.invoices import InvoiceManager
from fubble.core.billing import BillingEngine
from fubble.database.models import BillingPeriod, UsageEvent


router = APIRouter(prefix="/invoices", tags=["invoices"])


class InvoiceItemCreate(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    quantity: Optional[float] = None
    metric_name: Optional[str] = None
    unit_price: Optional[float] = None


class InvoiceCreate(BaseModel):
    customer_id: int
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    description: str
    metric_name: Optional[str]
    quantity: Optional[float]
    unit_price: float
    amount: float
    created_at: str

    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    # i really don't like this, but it's a workaround for the fact that the database fields are not always strings
    @root_validator(pre=True)
    def convert_datetimes(cls, values):
        # Handle both dictionary and model objects
        if not isinstance(values, dict):
            # If values is an ORM model, convert it to a dict first
            if hasattr(values, "__dict__"):
                # For ORM models that have __dict__
                values_dict = {}
                for field in [
                    "id",
                    "invoice_id",
                    "description",
                    "metric_name",
                    "quantity",
                    "unit_price",
                    "amount",
                    "created_at",
                ]:
                    if hasattr(values, field):
                        values_dict[field] = getattr(values, field)
                values = values_dict

        # Now process the dictionary
        if isinstance(values, dict):
            # Convert datetime to string for certain fields
            for field in ["created_at"]:
                if field in values and isinstance(values[field], datetime):
                    values[field] = values[field].isoformat()

        return values


class InvoiceResponse(BaseModel):
    id: int
    customer_id: int
    invoice_number: str
    status: str
    issue_date: str
    due_date: str
    amount: float
    paid_date: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    invoice_items: List[InvoiceItemResponse]

    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    @root_validator(pre=True)
    def convert_datetimes(cls, values):
        # Handle both dictionary and model objects
        if not isinstance(values, dict):
            # If values is an ORM model, convert it to a dict first
            if hasattr(values, "__dict__"):
                # For ORM models that have __dict__
                values_dict = {}
                for field in [
                    "id",
                    "customer_id",
                    "invoice_number",
                    "status",
                    "issue_date",
                    "due_date",
                    "amount",
                    "paid_date",
                    "notes",
                    "created_at",
                    "updated_at",
                    "invoice_items",
                ]:
                    if hasattr(values, field):
                        values_dict[field] = getattr(values, field)
                values = values_dict

        # Now process the dictionary
        if isinstance(values, dict):
            # Convert datetime to string for certain fields
            for field in [
                "issue_date",
                "due_date",
                "paid_date",
                "created_at",
                "updated_at",
            ]:
                if (
                    field in values
                    and isinstance(values[field], datetime)
                    and values[field] is not None
                ):
                    values[field] = values[field].isoformat()

        return values


class GenerateInvoicesRequest(BaseModel):
    start_date: str
    end_date: str
    customer_id: Optional[int] = None  # Added optional customer_id field


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice_data: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice."""
    invoice_manager = InvoiceManager(db)

    # Parse dates if provided
    issue_date = None
    if invoice_data.issue_date:
        try:
            issue_date = datetime.fromisoformat(invoice_data.issue_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid issue_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    due_date = None
    if invoice_data.due_date:
        try:
            due_date = datetime.fromisoformat(invoice_data.due_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    # Create the invoice
    invoice = invoice_manager.create_empty_invoice(
        customer_id=invoice_data.customer_id,
        issue_date=issue_date,
        due_date=due_date,
        notes=invoice_data.notes,
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create invoice. Please check that the customer exists.",
        )

    # Add invoice items if provided
    if invoice_data.items:
        for item_data in invoice_data.items:
            invoice_manager.add_invoice_item(
                invoice_id=invoice.id,
                description=item_data.description,
                amount=item_data.amount,
                quantity=item_data.quantity,
                metric_name=item_data.metric_name,
                unit_price=item_data.unit_price,
            )

    # Refresh the invoice to get the items
    db.refresh(invoice)

    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get an invoice by ID."""
    invoice_manager = InvoiceManager(db)
    invoice = invoice_manager.get_invoice(invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    return invoice


@router.get("/customer/{customer_id}", response_model=List[InvoiceResponse])
def get_customer_invoices(
    customer_id: int, status: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get invoices for a customer, optionally filtered by status."""
    invoice_manager = InvoiceManager(db)
    invoices = invoice_manager.get_customer_invoices(customer_id, status)

    return invoices


@router.put("/{invoice_id}/status", response_model=InvoiceResponse)
def update_invoice_status(
    invoice_id: int,
    status: str = Query(
        ..., description="New invoice status (draft, pending, paid, failed, void)"
    ),
    db: Session = Depends(get_db),
):
    """Update an invoice's status."""
    invoice_manager = InvoiceManager(db)
    invoice = invoice_manager.update_invoice_status(invoice_id, status)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or status update failed",
        )

    return invoice


@router.put("/{invoice_id}/finalize", response_model=InvoiceResponse)
def finalize_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Finalize an invoice (change status from draft to pending)."""
    invoice_manager = InvoiceManager(db)
    invoice = invoice_manager.finalize_invoice(invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice not found or cannot be finalized",
        )

    return invoice


@router.put("/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(
    invoice_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)
):
    """Void an invoice."""
    invoice_manager = InvoiceManager(db)
    invoice = invoice_manager.void_invoice(invoice_id, reason)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice not found or cannot be voided",
        )

    return invoice


@router.post("/{invoice_id}/items", response_model=InvoiceItemResponse)
def add_invoice_item(
    invoice_id: int, item_data: InvoiceItemCreate, db: Session = Depends(get_db)
):
    """Add an item to an invoice."""
    invoice_manager = InvoiceManager(db)

    item = invoice_manager.add_invoice_item(
        invoice_id=invoice_id,
        description=item_data.description,
        amount=item_data.amount,
        quantity=item_data.quantity,
        metric_name=item_data.metric_name,
        unit_price=item_data.unit_price,
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice not found or item could not be added",
        )

    return item


@router.delete("/{invoice_id}/items/{item_id}")
def remove_invoice_item(invoice_id: int, item_id: int, db: Session = Depends(get_db)):
    """Remove an item from an invoice."""
    invoice_manager = InvoiceManager(db)

    success = invoice_manager.remove_invoice_item(item_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item not found or could not be removed",
        )

    return {"message": "Item removed successfully"}


@router.post("/generate", response_model=List[InvoiceResponse])
def generate_invoices(
    request: Optional[GenerateInvoicesRequest] = None,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Generate invoices for all billing periods and/or usage within a date range.

    Can accept dates either as query parameters or in request body.
    If customer_id is provided, will only generate invoices for that customer.
    """
    # Use request body values if query params are not provided
    if request:
        if not start_date:
            start_date = request.start_date
        if not end_date:
            end_date = request.end_date
        if not customer_id and request.customer_id:
            customer_id = request.customer_id

    # Ensure we have both date parameters
    if not start_date or not end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both start_date and end_date are required",
        )

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

    # Debug logging
    logger = logging.getLogger("fubble-api")

    # Generate invoices using the date-range based approach
    billing_engine = BillingEngine(db)
    invoices = billing_engine.generate_invoices_for_period(
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        customer_id=customer_id,
    )

    logger.info(f"Generated {len(invoices)} invoices for the period")

    return invoices
