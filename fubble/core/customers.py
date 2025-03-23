from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from fubble.database.models import Customer, Subscription, Plan
from fubble.core.billing import BillingEngine


class CustomerManager:
    """
    Handles customer management operations, including subscriptions.
    """

    def __init__(self, db: Session):
        self.db = db
        self.billing_engine = BillingEngine(db)

    def create_customer(
        self,
        name: str,
        email: str,
        company_name: Optional[str] = None,
        billing_address: Optional[str] = None,
        payment_method_id: Optional[str] = None,
    ) -> Customer:
        """
        Creates a new customer.

        Args:
            name: The customer's name.
            email: The customer's email address.
            company_name: The customer's company name.
            billing_address: The customer's billing address.
            payment_method_id: ID for the customer's payment method.

        Returns:
            The created Customer object.
        """
        customer = Customer(
            name=name,
            email=email,
            company_name=company_name,
            billing_address=billing_address,
            payment_method_id=payment_method_id,
        )

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """
        Gets a customer by ID.

        Args:
            customer_id: The customer's ID.

        Returns:
            The Customer object if found, None otherwise.
        """
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """
        Gets a customer by email.

        Args:
            email: The customer's email address.

        Returns:
            The Customer object if found, None otherwise.
        """
        return self.db.query(Customer).filter(Customer.email == email).first()

    def update_customer(
        self, customer_id: int, update_data: Dict[str, Any]
    ) -> Optional[Customer]:
        """
        Updates a customer's details.

        Args:
            customer_id: The customer's ID.
            update_data: Dictionary of fields to update.

        Returns:
            The updated Customer object if found, None otherwise.
        """
        customer = self.get_customer(customer_id)
        if not customer:
            return None

        # Update customer fields
        for key, value in update_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        customer.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def create_subscription(
        self,
        customer_id: int,
        plan_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Subscription]:
        """
        Creates a new subscription for a customer.

        Args:
            customer_id: The customer's ID.
            plan_id: The ID of the pricing plan.
            start_date: When the subscription starts (defaults to now).
            end_date: When the subscription ends (None means ongoing).

        Returns:
            The created Subscription object if successful, None otherwise.
        """
        customer = self.get_customer(customer_id)
        if not customer:
            return None

        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            return None

        if start_date is None:
            start_date = datetime.utcnow()

        # Create the subscription
        subscription = Subscription(
            customer_id=customer_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        # Create billing periods for this subscription
        self.billing_engine.create_billing_periods(subscription)

        return subscription

    def cancel_subscription(
        self, subscription_id: int, end_date: Optional[datetime] = None
    ) -> Optional[Subscription]:
        """
        Cancels a subscription.

        Args:
            subscription_id: The subscription's ID.
            end_date: When the subscription should end (defaults to now).

        Returns:
            The updated Subscription object if found, None otherwise.
        """
        subscription = (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )

        if not subscription:
            return None

        if end_date is None:
            end_date = datetime.utcnow()

        subscription.is_active = False
        subscription.end_date = end_date
        subscription.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def get_active_subscriptions(self, customer_id: int) -> List[Subscription]:
        """
        Gets all active subscriptions for a customer.

        Args:
            customer_id: The customer's ID.

        Returns:
            List of active Subscription objects.
        """
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.customer_id == customer_id, Subscription.is_active == True
            )
            .all()
        )

    def get_subscription_history(self, customer_id: int) -> List[Subscription]:
        """
        Gets all subscriptions (active and inactive) for a customer.

        Args:
            customer_id: The customer's ID.

        Returns:
            List of all Subscription objects for the customer.
        """
        return (
            self.db.query(Subscription)
            .filter(Subscription.customer_id == customer_id)
            .order_by(Subscription.start_date.desc())
            .all()
        )
