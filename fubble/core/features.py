from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from sqlalchemy.orm import Session

from fubble.database.models import Feature, PlanFeature, CustomerFeature, Customer, Plan


class FeatureManager:
    """
    Manages feature entitlements for customers and plans.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_feature(
        self,
        name: str,
        display_name: str,
        description: str = None,
        is_active: bool = True,
    ) -> Feature:
        """
        Creates a new feature in the system.

        :param name: Unique identifier for the feature.
        :param display_name: Human-readable name.
        :param description: Description of what the feature provides.
        :param is_active: Whether the feature is active.
        :return: The created Feature object.
        """
        feature = Feature(
            name=name,
            display_name=display_name,
            description=description,
            is_active=is_active,
        )

        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)

        return feature

    def get_feature(self, feature_id_or_name: Union[int, str]) -> Optional[Feature]:
        """
        Gets a feature by ID or name.

        :param feature_id_or_name: Either the feature ID or name.
        :return: The Feature object if found, None otherwise.
        """
        if isinstance(feature_id_or_name, int):
            return (
                self.db.query(Feature).filter(Feature.id == feature_id_or_name).first()
            )
        else:
            return (
                self.db.query(Feature)
                .filter(Feature.name == feature_id_or_name)
                .first()
            )

    def get_all_features(self, active_only: bool = False) -> List[Feature]:
        """
        Gets all features in the system.

        :param active_only: Whether to only return active features.
        :return: List of Feature objects.
        """
        query = self.db.query(Feature)
        if active_only:
            query = query.filter(Feature.is_active == True)
        return query.all()

    def update_feature(
        self, feature_id: int, update_data: Dict[str, Any]
    ) -> Optional[Feature]:
        """
        Updates a feature's details.

        :param feature_id: The feature's ID.
        :param update_data: Dictionary of fields to update.
        :return: The updated Feature object if found, None otherwise.
        """
        feature = self.get_feature(feature_id)
        if not feature:
            return None

        # Update feature fields
        for key, value in update_data.items():
            if hasattr(feature, key) and key != "id":
                setattr(feature, key, value)

        feature.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(feature)

        return feature

    def assign_feature_to_plan(
        self,
        plan_id: int,
        feature_id: int,
        is_enabled: bool = True,
        limits: Dict[str, Any] = None,
    ) -> Optional[PlanFeature]:
        """
        Assigns a feature to a pricing plan.

        :param plan_id: The plan's ID.
        :param feature_id: The feature's ID.
        :param is_enabled: Whether the feature is enabled for this plan.
        :param limits: Optional limits for this feature (e.g., max_users: 5).
        :return: The created PlanFeature object if successful, None otherwise.
        """
        # Check if plan and feature exist
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        feature = self.get_feature(feature_id)

        if not plan or not feature:
            return None

        # Check if this assignment already exists
        existing = (
            self.db.query(PlanFeature)
            .filter(
                PlanFeature.plan_id == plan_id, PlanFeature.feature_id == feature_id
            )
            .first()
        )

        if existing:
            # Update existing
            existing.is_enabled = is_enabled
            existing.limits = limits
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new assignment
        plan_feature = PlanFeature(
            plan_id=plan_id, feature_id=feature_id, is_enabled=is_enabled, limits=limits
        )

        self.db.add(plan_feature)
        self.db.commit()
        self.db.refresh(plan_feature)

        return plan_feature

    def override_customer_feature(
        self,
        customer_id: int,
        feature_id: int,
        is_enabled: bool = True,
        override_limits: Dict[str, Any] = None,
    ) -> Optional[CustomerFeature]:
        """
        Creates or updates a feature override for a specific customer.

        :param customer_id: The customer's ID.
        :param feature_id: The feature's ID.
        :param is_enabled: Whether the feature is enabled for this customer.
        :param override_limits: Optional limits that override plan limits.

        :return: The created/updated CustomerFeature object if successful, None otherwise.
        """
        # Check if customer and feature exist
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        feature = self.get_feature(feature_id)

        if not customer or not feature:
            return None

        # Check if this override already exists
        existing = (
            self.db.query(CustomerFeature)
            .filter(
                CustomerFeature.customer_id == customer_id,
                CustomerFeature.feature_id == feature_id,
            )
            .first()
        )

        if existing:
            # Update existing
            existing.is_enabled = is_enabled
            existing.override_limits = override_limits
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new override
        customer_feature = CustomerFeature(
            customer_id=customer_id,
            feature_id=feature_id,
            is_enabled=is_enabled,
            override_limits=override_limits,
        )

        self.db.add(customer_feature)
        self.db.commit()
        self.db.refresh(customer_feature)

        return customer_feature

    def check_customer_feature_access(
        self, customer_id: int, feature_name: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks if a customer has access to a specific feature.

        :param customer_id: The customer's ID.
        :param feature_name: The feature's name.
        :return: Tuple of (has_access, limits) where has_access is a boolean and
            limits is a dictionary of any limits on the feature.
        """
        feature = self.get_feature(feature_name)
        if not feature or not feature.is_active:
            return (False, None)

        # Check for customer override
        customer_override = (
            self.db.query(CustomerFeature)
            .filter(
                CustomerFeature.customer_id == customer_id,
                CustomerFeature.feature_id == feature.id,
            )
            .first()
        )

        if customer_override is not None:
            # Customer has an explicit override
            return (customer_override.is_enabled, customer_override.override_limits)

        # No override, check the customer's subscription plan
        # Get active subscription(s) for the customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return (False, None)

        active_subscriptions = [
            sub
            for sub in customer.subscriptions
            if sub.is_active
            and (sub.end_date is None or sub.end_date >= datetime.utcnow())
        ]

        if not active_subscriptions:
            return (False, None)

        # Check each subscription's plan for the feature
        for subscription in active_subscriptions:
            plan_feature = (
                self.db.query(PlanFeature)
                .filter(
                    PlanFeature.plan_id == subscription.plan_id,
                    PlanFeature.feature_id == feature.id,
                )
                .first()
            )

            if plan_feature and plan_feature.is_enabled:
                # Customer has access through their plan
                return (True, plan_feature.limits)

        # Customer doesn't have access to this feature
        return (False, None)
