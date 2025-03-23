from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from fubble.database.models import UsageEvent, Customer, Subscription, Metric
from fubble.database.models import BillingPeriod


class UsageManager:
    """
    Handles tracking and managing usage events for customers.
    """

    def __init__(self, db: Session):
        self.db = db

    def record_usage(
        self,
        customer_id: int,
        metric_name: str,
        quantity: float,
        subscription_id: Optional[int] = None,
        event_time: Optional[datetime] = None,
        properties: Optional[Dict[str, Any]] = None,
        billing_period_id: Optional[int] = None,
    ) -> UsageEvent:
        """
        Records a usage event for a customer.

        Args:
            customer_id: The ID of the customer.
            metric_name: The name of the metric being tracked.
            quantity: The amount of usage to record.
            subscription_id: Optional ID of the subscription this usage is for.
            event_time: When the usage occurred (defaults to now).
            properties: Additional properties/dimensions for the usage event.
            billing_period_id: Optional billing period ID if relevant.

        Returns:
            The created UsageEvent object.
        """
        # Verify the customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")

        # Verify the subscription if provided
        subscription = None
        if subscription_id:
            subscription = (
                self.db.query(Subscription)
                .filter(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id,
                )
                .first()
            )
            if not subscription:
                raise ValueError(
                    f"Subscription with ID {subscription_id} not found for customer {customer_id}"
                )

        # Get metric ID if it exists
        metric = self.db.query(Metric).filter(Metric.name == metric_name).first()
        metric_id = metric.id if metric else None

        # Find the appropriate billing period if not provided but subscription is available
        if not billing_period_id and subscription:
            now = event_time or datetime.utcnow()

            billing_period = (
                self.db.query(BillingPeriod)
                .filter(
                    BillingPeriod.subscription_id == subscription_id,
                    BillingPeriod.start_date <= now,
                    BillingPeriod.end_date >= now,
                )
                .first()
            )
            if billing_period:
                billing_period_id = billing_period.id

        # Create the usage event
        usage_event = UsageEvent(
            customer_id=customer_id,
            subscription_id=subscription_id,
            billing_period_id=billing_period_id,
            metric_name=metric_name,
            metric_id=metric_id,
            quantity=quantity,
            event_time=event_time or datetime.utcnow(),
            properties=properties or {},
        )

        self.db.add(usage_event)
        self.db.commit()
        self.db.refresh(usage_event)

        return usage_event

    def get_usage_for_period(
        self,
        customer_id: int,
        start_date: datetime,
        end_date: datetime,
        metric_name: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Gets aggregated usage for a customer during a specific period.

        Args:
            customer_id: The ID of the customer.
            start_date: Start of the period.
            end_date: End of the period.
            metric_name: Optional metric name to filter by.

        Returns:
            Dictionary mapping metric names to their total usage quantity.
        """
        # Build the query
        query = self.db.query(UsageEvent).filter(
            UsageEvent.customer_id == customer_id,
            UsageEvent.event_time >= start_date,
            UsageEvent.event_time <= end_date,
        )

        # Apply metric filter if provided
        if metric_name:
            query = query.filter(UsageEvent.metric_name == metric_name)

        # Execute query
        usage_events = query.all()

        # Aggregate usage by metric
        usage_by_metric = {}
        for event in usage_events:
            if event.metric_name not in usage_by_metric:
                usage_by_metric[event.metric_name] = 0
            usage_by_metric[event.metric_name] += event.quantity

        return usage_by_metric
