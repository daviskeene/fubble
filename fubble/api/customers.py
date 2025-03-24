from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, root_validator
from datetime import datetime

from fubble.database.connection import get_db
from fubble.core.customers import CustomerManager


router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    payment_method_id: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    payment_method_id: Optional[str] = None


class SubscriptionCreate(BaseModel):
    plan_id: int
    start_date: Optional[str] = None  # ISO format date
    end_date: Optional[str] = None  # ISO format date


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    payment_method_id: Optional[str] = None
    created_at: str  # ISO format date
    updated_at: str  # ISO format date

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
                    "name",
                    "email",
                    "company_name",
                    "billing_address",
                    "payment_method_id",
                    "created_at",
                    "updated_at",
                ]:
                    if hasattr(values, field):
                        values_dict[field] = getattr(values, field)
                values = values_dict

        # Now process the dictionary
        if isinstance(values, dict):
            # Convert datetime to string for certain fields
            for field in ["created_at", "updated_at"]:
                if field in values and isinstance(values[field], datetime):
                    values[field] = values[field].isoformat()

        return values


class SubscriptionResponse(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    start_date: str  # ISO format date
    end_date: Optional[str] = None  # ISO format date
    is_active: bool
    created_at: str  # ISO format date
    updated_at: str  # ISO format date

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
                    "plan_id",
                    "start_date",
                    "end_date",
                    "is_active",
                    "created_at",
                    "updated_at",
                ]:
                    if hasattr(values, field):
                        values_dict[field] = getattr(values, field)
                values = values_dict

        # Now process the dictionary
        if isinstance(values, dict):
            # Convert datetime to string for certain fields
            for field in ["start_date", "end_date", "created_at", "updated_at"]:
                if field in values and isinstance(values[field], datetime):
                    values[field] = values[field].isoformat()

        return values


@router.get("/")
def get_customers(db: Session = Depends(get_db)):
    """Get all customers."""
    customer_manager = CustomerManager(db)
    return customer_manager.get_customers()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    customer_manager = CustomerManager(db)

    # Check if customer with this email already exists
    existing_customer = customer_manager.get_customer_by_email(customer_data.email)
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )

    customer = customer_manager.create_customer(
        name=customer_data.name,
        email=customer_data.email,
        company_name=customer_data.company_name,
        billing_address=customer_data.billing_address,
        payment_method_id=customer_data.payment_method_id,
    )

    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a customer by ID."""
    customer_manager = CustomerManager(db)
    customer = customer_manager.get_customer(customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int, customer_data: CustomerUpdate, db: Session = Depends(get_db)
):
    """Update a customer."""
    customer_manager = CustomerManager(db)

    # Check if customer exists
    existing_customer = customer_manager.get_customer(customer_id)
    if not existing_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # If email is being updated, check for uniqueness
    if customer_data.email and customer_data.email != existing_customer.email:
        email_customer = customer_manager.get_customer_by_email(customer_data.email)
        if email_customer and email_customer.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists",
            )

    # Convert Pydantic model to dictionary, excluding None values
    update_data = customer_data.dict(exclude_unset=True)

    customer = customer_manager.update_customer(customer_id, update_data)
    return customer


@router.post("/{customer_id}/subscriptions", response_model=SubscriptionResponse)
def create_subscription(
    customer_id: int,
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    """Create a subscription for a customer."""
    customer_manager = CustomerManager(db)

    # Check if customer exists
    customer = customer_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Parse dates if provided
    start_date = None
    if subscription_data.start_date:
        try:
            start_date = datetime.fromisoformat(subscription_data.start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    end_date = None
    if subscription_data.end_date:
        try:
            end_date = datetime.fromisoformat(subscription_data.end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    # Create subscription
    subscription = customer_manager.create_subscription(
        customer_id=customer_id,
        plan_id=subscription_data.plan_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create subscription. Please check that the plan exists.",
        )

    return subscription


@router.get("/{customer_id}/subscriptions", response_model=List[SubscriptionResponse])
def get_customer_subscriptions(
    customer_id: int, active_only: bool = True, db: Session = Depends(get_db)
):
    """Get subscriptions for a customer."""
    customer_manager = CustomerManager(db)

    # Check if customer exists
    customer = customer_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    if active_only:
        subscriptions = customer_manager.get_active_subscriptions(customer_id)
    else:
        subscriptions = customer_manager.get_subscription_history(customer_id)

    return subscriptions


@router.put("/{customer_id}/subscriptions/{subscription_id}/cancel")
def cancel_subscription(
    customer_id: int,
    subscription_id: int,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Cancel a subscription."""
    customer_manager = CustomerManager(db)

    # Parse end date if provided
    parsed_end_date = None
    if end_date:
        try:
            parsed_end_date = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).",
            )

    # Cancel subscription
    subscription = customer_manager.cancel_subscription(
        subscription_id=subscription_id, end_date=parsed_end_date
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    # Verify this subscription belongs to the customer
    if subscription.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription does not belong to this customer",
        )

    return {"message": "Subscription canceled successfully"}
