import pytest
import random
from datetime import datetime, timedelta
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fubble.database.models import (
    Customer,
    Subscription,
    Plan,
    BillingPeriod,
    UsageEvent,
)
from fubble.core.events import EventTracker
from fubble.app import app


@pytest.fixture
def db(test_db_session):
    return test_db_session


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def setup_test_data(db):
    # Create test customer with valid fields only
    customer = Customer(
        id=random.randint(1, 1000000),
        name="Test Customer",
        email="test@example.com",
        company_name="Test Company",
    )
    db.add(customer)

    # Create test plan
    plan = Plan(
        name="Test Plan",
        description="Test Plan Description",
        billing_frequency="monthly",
    )
    db.add(plan)

    # Commit to get IDs
    db.commit()

    # Create subscription
    now = datetime.utcnow()
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        start_date=now - timedelta(days=30),
        is_active=True,
    )
    db.add(subscription)
    db.commit()

    # Create billing period
    billing_period = BillingPeriod(
        subscription_id=subscription.id,
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=30),
    )
    db.add(billing_period)
    db.commit()

    return {
        "customer": customer,
        "plan": plan,
        "subscription": subscription,
        "billing_period": billing_period,
    }


class TestEventTracker:
    """Tests for the core EventTracker functionality"""

    def test_track_event(self, db, setup_test_data):
        customer = setup_test_data["customer"]
        tracker = EventTracker(db)

        # Test with minimal parameters
        event = tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=10
        )

        assert event.id is not None
        assert event.customer_id == customer.id
        assert event.metric_name == "api_calls"
        assert event.quantity == 10
        assert event.event_time is not None
        assert event.properties == {}
        assert event.billing_period_id == setup_test_data["billing_period"].id

        # Test with all parameters
        properties = {"path": "/test", "method": "GET"}
        custom_time = datetime.utcnow() - timedelta(hours=2)

        event = tracker.track_event(
            customer_id=customer.id,
            metric_name="storage_gb",
            quantity=5.5,
            event_time=custom_time,
            properties=properties,
        )

        assert event.id is not None
        assert event.customer_id == customer.id
        assert event.metric_name == "storage_gb"
        assert event.quantity == 5.5
        assert event.event_time == custom_time
        assert event.properties == properties
        assert event.billing_period_id == setup_test_data["billing_period"].id

    def test_batch_track_events(self, db, setup_test_data):
        customer = setup_test_data["customer"]
        tracker = EventTracker(db)

        custom_time = datetime.utcnow() - timedelta(hours=1)
        events_data = [
            {"customer_id": customer.id, "metric_name": "api_calls", "quantity": 5},
            {
                "customer_id": customer.id,
                "metric_name": "storage_gb",
                "quantity": 2.5,
                "event_time": custom_time,
                "properties": {"type": "image"},
            },
        ]

        events = tracker.batch_track_events(events_data)

        assert len(events) == 2
        assert events[0].metric_name == "api_calls"
        assert events[0].quantity == 5
        assert events[1].metric_name == "storage_gb"
        assert events[1].quantity == 2.5
        assert events[1].event_time == custom_time
        assert events[1].properties == {"type": "image"}

    def test_get_usage_by_metric(self, db, setup_test_data):
        customer = setup_test_data["customer"]
        tracker = EventTracker(db)

        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Create test events
        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=10
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=15
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="storage_gb", quantity=5.5
        )

        # Get usage data
        usage = tracker.get_usage_by_metric(
            customer_id=customer.id, start_date=yesterday, end_date=tomorrow
        )

        assert "api_calls" in usage
        assert "storage_gb" in usage
        assert usage["api_calls"] == 25
        assert usage["storage_gb"] == 5.5


class TestEventsAPI:
    """Tests for the events API endpoints"""

    def test_track_event_api(self, client, setup_test_data):
        customer = setup_test_data["customer"]

        # Test with minimal parameters
        response = client.post(
            "/events/",
            json={
                "customer_id": customer.id,
                "metric_name": "api_calls",
                "quantity": 10,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer.id
        assert data["metric_name"] == "api_calls"
        assert data["quantity"] == 10

        # Test with all parameters
        custom_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        properties = {"path": "/test", "method": "GET"}

        response = client.post(
            "/events/",
            json={
                "customer_id": customer.id,
                "metric_name": "storage_gb",
                "quantity": 5.5,
                "event_time": custom_time,
                "properties": properties,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer.id
        assert data["metric_name"] == "storage_gb"
        assert data["quantity"] == 5.5
        assert data["properties"] == properties

    def test_batch_track_events_api(self, client, setup_test_data):
        customer = setup_test_data["customer"]

        custom_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        response = client.post(
            "/events/batch",
            json={
                "events": [
                    {
                        "customer_id": customer.id,
                        "metric_name": "api_calls",
                        "quantity": 5,
                    },
                    {
                        "customer_id": customer.id,
                        "metric_name": "storage_gb",
                        "quantity": 2.5,
                        "event_time": custom_time,
                        "properties": {"type": "image"},
                    },
                ]
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2
        assert data[0]["metric_name"] == "api_calls"
        assert data[0]["quantity"] == 5
        assert data[1]["metric_name"] == "storage_gb"
        assert data[1]["quantity"] == 2.5
        assert data[1]["properties"] == {"type": "image"}

    def test_get_customer_events_api(self, client, setup_test_data, db):
        customer = setup_test_data["customer"]
        tracker = EventTracker(db)

        # Create test events
        now = datetime.utcnow()
        start_date = (now - timedelta(days=1)).isoformat()
        end_date = (now + timedelta(days=1)).isoformat()

        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=10
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=15
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="storage_gb", quantity=5.5
        )

        # Test getting all events
        response = client.get(
            f"/events/customers/{customer.id}",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test filtering by metric
        response = client.get(
            f"/events/customers/{customer.id}",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "metric_name": "api_calls",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(event["metric_name"] == "api_calls" for event in data)

    def test_get_customer_usage_api(self, client, setup_test_data, db):
        customer = setup_test_data["customer"]
        tracker = EventTracker(db)

        # Create test events
        now = datetime.utcnow()
        start_date = (now - timedelta(days=1)).isoformat()
        end_date = (now + timedelta(days=1)).isoformat()

        # Create events in a transaction
        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=10
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="api_calls", quantity=15
        )
        tracker.track_event(
            customer_id=customer.id, metric_name="storage_gb", quantity=5.5
        )

        # Use a separate API test client to avoid session conflicts
        response = client.get(
            f"/events/customers/{customer.id}/usage",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200
        data = response.json()
        print(f"Data received: {data}")
        assert "api_calls" in data
        assert "storage_gb" in data
        assert data["api_calls"] == 15
        assert data["storage_gb"] == 5.5

    def test_invalid_date_format(self, client, setup_test_data):
        customer = setup_test_data["customer"]

        # Test invalid event_time
        response = client.post(
            "/events/",
            json={
                "customer_id": customer.id,
                "metric_name": "api_calls",
                "quantity": 10,
                "event_time": "invalid-date",
            },
        )

        assert response.status_code == 400
        assert "Invalid event_time format" in response.json()["detail"]

        # Test invalid start_date
        response = client.get(
            f"/events/customers/{customer.id}",
            params={
                "start_date": "invalid-date",
                "end_date": datetime.utcnow().isoformat(),
            },
        )

        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]
