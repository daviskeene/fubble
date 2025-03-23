from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, root_validator
from datetime import datetime

from fubble.database.connection import get_db
from fubble.core.plans import PlanManager


router = APIRouter(prefix="/plans", tags=["plans"])


class PriceComponentCreate(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    pricing_type: str = Field(..., description="flat, tiered, volume, or package")
    pricing_details: Dict[str, Any]


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    billing_frequency: str = Field(..., description="monthly, quarterly, or yearly")
    price_components: Optional[List[PriceComponentCreate]] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    billing_frequency: Optional[str] = Field(
        None, description="monthly, quarterly, or yearly"
    )
    is_active: Optional[bool] = None


class PriceComponentResponse(BaseModel):
    id: int
    plan_id: int
    metric_name: str
    display_name: str
    pricing_type: str
    pricing_details: Dict[str, Any]
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
                    "plan_id",
                    "metric_name",
                    "display_name",
                    "pricing_type",
                    "pricing_details",
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


class PlanResponse(BaseModel):
    id: int
    name: str
    description: str
    billing_frequency: str
    is_active: bool
    created_at: str  # ISO format date
    updated_at: str  # ISO format date
    price_components: List[PriceComponentResponse]

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
                    "description",
                    "billing_frequency",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "price_components",
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


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(plan_data: PlanCreate, db: Session = Depends(get_db)):
    """Create a new pricing plan."""
    plan_manager = PlanManager(db)

    # Convert price components to the format expected by the manager
    price_components = None
    if plan_data.price_components:
        price_components = [comp.dict() for comp in plan_data.price_components]

    # Create the plan
    plan = plan_manager.create_plan(
        name=plan_data.name,
        description=plan_data.description,
        billing_frequency=plan_data.billing_frequency,
        price_components=price_components,
    )

    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a plan by ID."""
    plan_manager = PlanManager(db)
    plan = plan_manager.get_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    return plan


@router.get("/", response_model=List[PlanResponse])
def get_plans(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all plans, optionally filtering to active only."""
    plan_manager = PlanManager(db)

    if active_only:
        plans = plan_manager.get_all_active_plans()
    else:
        plans = db.query(plan_manager.__class__.__module__ + ".Plan").all()

    return plans


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, plan_data: PlanUpdate, db: Session = Depends(get_db)):
    """Update a plan."""
    plan_manager = PlanManager(db)

    # Check if plan exists
    existing_plan = plan_manager.get_plan(plan_id)
    if not existing_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Convert Pydantic model to dictionary, excluding None values
    update_data = plan_data.dict(exclude_unset=True)

    plan = plan_manager.update_plan(plan_id, update_data)
    return plan


@router.put("/{plan_id}/deactivate")
def deactivate_plan(plan_id: int, db: Session = Depends(get_db)):
    """Deactivate a plan."""
    plan_manager = PlanManager(db)

    plan = plan_manager.deactivate_plan(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    return {"message": "Plan deactivated successfully"}


@router.post("/{plan_id}/components", response_model=PriceComponentResponse)
def add_price_component(
    plan_id: int, component_data: PriceComponentCreate, db: Session = Depends(get_db)
):
    """Add a price component to a plan."""
    plan_manager = PlanManager(db)

    component = plan_manager.add_price_component(
        plan_id=plan_id,
        metric_name=component_data.metric_name,
        display_name=component_data.display_name,
        pricing_type=component_data.pricing_type,
        pricing_details=component_data.pricing_details,
    )

    if not component:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add price component. Check that the plan exists and pricing type is valid.",
        )

    return component


@router.delete("/{plan_id}/components/{component_id}")
def remove_price_component(
    plan_id: int, component_id: int, db: Session = Depends(get_db)
):
    """Remove a price component from a plan."""
    plan_manager = PlanManager(db)

    # First check if plan exists
    plan = plan_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Now attempt to remove the component
    success = plan_manager.remove_price_component(component_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price component not found or could not be removed",
        )

    return {"message": "Price component removed successfully"}


@router.post("/{plan_id}/components/tiered", response_model=Dict[str, Any])
def create_tiered_pricing_details(
    plan_id: int, tiers: List[Dict[str, Any]], db: Session = Depends(get_db)
):
    """Create pricing details for a tiered pricing component."""
    plan_manager = PlanManager(db)

    # Validate the plan exists
    plan = plan_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Create pricing details
    pricing_details = plan_manager.create_tiered_pricing_details(tiers)

    return pricing_details


@router.post("/{plan_id}/components/volume", response_model=Dict[str, Any])
def create_volume_pricing_details(
    plan_id: int, tiers: List[Dict[str, Any]], db: Session = Depends(get_db)
):
    """Create pricing details for a volume pricing component."""
    plan_manager = PlanManager(db)

    # Validate the plan exists
    plan = plan_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Create pricing details
    pricing_details = plan_manager.create_volume_pricing_details(tiers)

    return pricing_details


@router.post("/{plan_id}/components/package", response_model=Dict[str, Any])
def create_package_pricing_details(
    plan_id: int,
    package_size: int = Query(..., description="Size of the package"),
    package_price: float = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """Create pricing details for a package pricing component."""
    plan_manager = PlanManager(db)

    # Validate the plan exists
    plan = plan_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Create pricing details
    pricing_details = plan_manager.create_package_pricing_details(
        package_size, package_price
    )

    return pricing_details


@router.post("/{plan_id}/components/flat", response_model=Dict[str, Any])
def create_flat_pricing_details(
    plan_id: int, amount: float = Query(..., gt=0), db: Session = Depends(get_db)
):
    """Create pricing details for a flat pricing component."""
    plan_manager = PlanManager(db)

    # Validate the plan exists
    plan = plan_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    # Create pricing details
    pricing_details = plan_manager.create_flat_pricing_details(amount)

    return pricing_details
