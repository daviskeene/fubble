from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session

from fubble.database.models import Plan, PriceComponent, PricingType, BillingFrequency


class PlanManager:
    """
    Handles pricing plan management and operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_plan(
        self,
        name: str,
        description: str,
        billing_frequency: str,
        price_components: List[Dict[str, Any]] = None,
    ) -> Plan:
        """
        Creates a new pricing plan.

        :param name: The name of the plan.
        :param description: Description of the plan.
        :param billing_frequency: Frequency of billing (monthly, quarterly, yearly).
        :param price_components: List of price component specifications.
        :return: The created Plan object.
        """
        # Ensure valid billing frequency
        if billing_frequency not in ["monthly", "quarterly", "yearly"]:
            billing_frequency = "monthly"

        # Create the plan
        plan = Plan(
            name=name,
            description=description,
            billing_frequency=billing_frequency,
            is_active=True,
        )

        self.db.add(plan)
        self.db.flush()  # Get plan ID without committing transaction

        # Add price components if provided
        if price_components:
            for component_data in price_components:
                component = PriceComponent(
                    plan_id=plan.id,
                    metric_name=component_data["metric_name"],
                    display_name=component_data["display_name"],
                    pricing_type=component_data["pricing_type"],
                    pricing_details=component_data["pricing_details"],
                )
                self.db.add(component)

        self.db.commit()
        self.db.refresh(plan)

        return plan

    def get_plan(self, plan_id: int) -> Optional[Plan]:
        """
        Gets a plan by ID.

        :param plan_id: The plan's ID.
        :return: The Plan object if found, None otherwise.
        """
        return self.db.query(Plan).filter(Plan.id == plan_id).first()

    def get_all_active_plans(self) -> List[Plan]:
        """
        Gets all active pricing plans.

        :return: List of active Plan objects.
        """
        return self.db.query(Plan).filter(Plan.is_active == True).all()

    def update_plan(self, plan_id: int, update_data: Dict[str, Any]) -> Optional[Plan]:
        """
        Updates a plan's details.

        :param plan_id: The plan's ID.
        :param update_data: Dictionary of fields to update.
        :return: The updated Plan object if found, None otherwise.
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # Update plan fields
        for key, value in update_data.items():
            if hasattr(plan, key) and key != "id":
                setattr(plan, key, value)

        plan.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(plan)

        return plan

    def deactivate_plan(self, plan_id: int) -> Optional[Plan]:
        """
        Deactivates a pricing plan.

        :param plan_id: The plan's ID.
        :return: The deactivated Plan object if found, None otherwise.
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        plan.is_active = False
        plan.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(plan)

        return plan

    def add_price_component(
        self,
        plan_id: int,
        metric_name: str,
        display_name: str,
        pricing_type: str,
        pricing_details: Dict[str, Any],
    ) -> Optional[PriceComponent]:
        """
        Adds a price component to a plan.

        :param plan_id: The plan's ID.
        :param metric_name: The name of the metric.
        :param display_name: Display name for the metric.
        :param pricing_type: Type of pricing (flat, tiered, volume, package).
        :param pricing_details: Dictionary with pricing specifications.

        :return: The created PriceComponent if successful, None otherwise.
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # Validate pricing type
        if pricing_type not in ["flat", "tiered", "volume", "package"]:
            return None

        # Create price component
        component = PriceComponent(
            plan_id=plan_id,
            metric_name=metric_name,
            display_name=display_name,
            pricing_type=pricing_type,
            pricing_details=pricing_details,
        )

        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)

        return component

    def remove_price_component(self, component_id: int) -> bool:
        """
        Removes a price component from a plan.

        :param component_id: The component's ID.
        :return: True if successful, False otherwise.
        """
        component = (
            self.db.query(PriceComponent)
            .filter(PriceComponent.id == component_id)
            .first()
        )

        if not component:
            return False

        self.db.delete(component)
        self.db.commit()

        return True

    def create_tiered_pricing_details(
        self, tiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Helper method to create proper tiered pricing details.

        :param tiers: List of tier definitions with keys:
            - start: Start of tier (units)
            - end: End of tier (units, can be None for unlimited)
            - price: Price per unit in this tier
        :return: Pricing details dictionary for a tiered pricing component.
        """
        return {"tiers": tiers}

    def create_volume_pricing_details(
        self, tiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Helper method to create proper volume pricing details.

        :param tiers: List of tier definitions with keys:
            - start: Start of tier (units)
            - price: Price per unit when total usage is in this tier
        :return: Pricing details dictionary for a volume pricing component.
        """
        return {"tiers": tiers}

    def create_package_pricing_details(
        self, package_size: int, package_price: float
    ) -> Dict[str, Any]:
        """
        Helper method to create proper package pricing details.

        :param package_size: Number of units in a package.
        :param package_price: Price per package.
        :return: Pricing details dictionary for a package pricing component.
        """
        return {"package_size": package_size, "package_price": package_price}

    def create_flat_pricing_details(self, amount: float) -> Dict[str, Any]:
        """
        Helper method to create proper flat pricing details.

        :param amount: The flat fee amount.
        :return: Pricing details dictionary for a flat pricing component.
        """
        return {"amount": amount}
