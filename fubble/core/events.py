from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from fubble.database.models import Customer, BillingPeriod, UsageEvent


class EventTracker:
    """
    Handles recording and processing of usage events.
    """

    def __init__(self, db: Session):
        self.db = db

    def track_event(
        self,
        customer_id: int,
        metric_name: str,
        quantity: float,
        event_time: Optional[datetime] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UsageEvent:
        """
        Records a new usage event for a customer.

        :param customer_id: The ID of the customer.
        :param metric_name: The name of the metric being tracked (e.g., "api_calls", "storage_gb").
        :param quantity: The quantity of usage.
        :param event_time: The time the event occurred (defaults to now).
        :param properties: Additional properties to store with the event.
        :return: The created UsageEvent object.
        """
        if event_time is None:
            event_time = datetime.utcnow()

        if properties is None:
            properties = {}

        # Find the appropriate billing period for this event
        billing_period = self._find_billing_period(customer_id, event_time)

        # Create the usage event
        usage_event = UsageEvent(
            customer_id=customer_id,
            billing_period_id=billing_period.id if billing_period else None,
            metric_name=metric_name,
            quantity=quantity,
            event_time=event_time,
            properties=properties,
        )

        self.db.add(usage_event)
        self.db.commit()

        return usage_event

    def batch_track_events(self, events: List[Dict[str, Any]]) -> List[UsageEvent]:
        """
        Records multiple usage events in a batch.

        :param events: List of event dictionaries with keys:
            - customer_id: ID of the customer
            - metric_name: Name of the metric
            - quantity: Quantity of usage
            - event_time: (Optional) Time of the event
            - properties: (Optional) Additional properties
        :return: List of created UsageEvent objects.
        """
        created_events = []

        for event_data in events:
            customer_id = event_data["customer_id"]
            metric_name = event_data["metric_name"]
            quantity = event_data["quantity"]
            event_time = event_data.get("event_time", datetime.utcnow())
            properties = event_data.get("properties", {})

            event = self.track_event(
                customer_id=customer_id,
                metric_name=metric_name,
                quantity=quantity,
                event_time=event_time,
                properties=properties,
            )

            created_events.append(event)

        return created_events

    def get_usage_by_metric(
        self, customer_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Get total usage by metric for a customer in a given time period

        :param customer_id: The ID of the customer.
        :param start_date: The start of the period.
        :param end_date: The end of the period.
        :return: A dictionary mapping metric names to total usage.
        """
        result = (
            self.db.query(
                UsageEvent.metric_name, func.sum(UsageEvent.quantity).label("total")
            )
            .filter(
                UsageEvent.customer_id == customer_id,
                UsageEvent.event_time >= start_date,
                UsageEvent.event_time <= end_date,
            )
            .group_by(UsageEvent.metric_name)
            .all()
        )

        # Convert to dictionary
        usage_data = {item.metric_name: item.total for item in result}

        return usage_data

    def _find_billing_period(
        self, customer_id: int, event_time: datetime
    ) -> Optional[BillingPeriod]:
        """
        Finds the appropriate billing period for a customer at a given time.

        :param customer_id: The ID of the customer.
        :param event_time: The time to find a billing period for.
        :return: The matching BillingPeriod or None if not found.
        """
        # First, verify customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        # Find active subscriptions for this customer
        subscriptions = [
            sub
            for sub in customer.subscriptions
            if sub.is_active
            and (sub.start_date <= event_time)
            and (sub.end_date is None or sub.end_date >= event_time)
        ]

        if not subscriptions:
            return None

        # For each subscription, find the billing period that contains the event time
        for subscription in subscriptions:
            billing_period = (
                self.db.query(BillingPeriod)
                .filter(
                    BillingPeriod.subscription_id == subscription.id,
                    BillingPeriod.start_date <= event_time,
                    BillingPeriod.end_date >= event_time,
                )
                .first()
            )

            if billing_period:
                return billing_period

        return None
