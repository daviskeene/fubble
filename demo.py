"""
Fubble Demo Script

This script demonstrates how to use Fubble for usage-based billing:
1. Company A sets up Fubble to handle their API billing
2. Company A creates pricing plans for their API
3. Consumer 1 and Consumer 2 subscribe to the API
4. API usage events are recorded for both consumers
5. Invoices are generated based on the recorded usage
"""

import requests
import os
from datetime import datetime, timedelta
import random
import logging

from fubble.database.connection import get_db
from fubble.database.models import Customer, Plan, Subscription, UsageEvent, Invoice, PriceComponent, InvoiceItem, CommitmentTier, CreditBalance, CreditTransaction, Metric, BillingPeriod

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fubble-demo")


class FubbleDemo:
    """Demonstration of Fubble usage-based billing for API services."""

    def __init__(self, base_url="http://localhost:8000"):
        """Initialize the demo with the Fubble API endpoint."""
        self.base_url = base_url
        self.customers = {}  # Will store customer IDs
        self.plans = {}  # Will store plan IDs
        self.subscriptions = {}  # Will store subscription IDs
        logger.info(f"Initialized Fubble demo with API at {base_url}")

    def run_demo(self):
        """Run the full demonstration workflow."""
        logger.info("Starting Fubble demonstration")

        self.clean_db()

        # Step 1: Create customers
        self.create_customers()

        # Step 2: Create pricing plans
        self.create_pricing_plans()

        # Step 3: Create subscriptions for consumers
        self.create_subscriptions()

        # Step 4: Record API usage events
        self.simulate_api_usage()

        # Step 5: Generate invoices
        self.generate_invoices()

        logger.info("Fubble demonstration completed successfully")

    def clean_db(self):
        """Clean the database before running the demo."""
        logger.info("Cleaning database...")
        # Remove all customers, plans, subscriptions, and events
        db = next(get_db())
        # Remove all info from the database
        db.query(Customer).delete()
        db.query(Plan).delete()
        db.query(Subscription).delete()
        db.query(UsageEvent).delete()
        db.query(Invoice).delete()
        db.query(PriceComponent).delete()
        db.query(InvoiceItem).delete()
        db.query(CommitmentTier).delete()
        db.query(CreditBalance).delete()
        db.query(CreditTransaction).delete()
        db.query(Metric).delete()
        db.query(BillingPeriod).delete()
        # Commit the changes
        db.commit()
        logger.info("Database cleanup completed")

    def create_customers(self):
        """Create customers in the Fubble system."""
        logger.info("Creating customers in Fubble...")

        # Create Company A (the API provider)
        company_a = {
            "name": "Company A - API Provider",
            "email": "billing@companya.com",
            "company_name": "Company A Inc.",
            "billing_address": "123 Tech Park, San Francisco, CA 94105",
            "payment_method_id": "pm_card_visa",
        }

        # Create Consumer 1
        consumer_1 = {
            "name": "Consumer 1 - Startup Client",
            "email": "finance@consumer1.com",
            "company_name": "Consumer 1 LLC",
            "billing_address": "456 Startup Ave, Palo Alto, CA 94301",
            "payment_method_id": "pm_card_mastercard",
        }

        # Create Consumer 2
        consumer_2 = {
            "name": "Consumer 2 - Enterprise Client",
            "email": "accounts@consumer2.com",
            "company_name": "Consumer 2 Corp",
            "billing_address": "789 Corporate Blvd, San Jose, CA 95110",
            "payment_method_id": "pm_card_amex",
        }

        # Make API calls to create the customers
        customers_to_create = {
            "company_a": company_a,
            "consumer_1": consumer_1,
            "consumer_2": consumer_2,
        }

        for key, customer_data in customers_to_create.items():
            logger.info(f"Creating customer: {customer_data['name']}")
            try:
                response = requests.post(
                    f"{self.base_url}/customers/", json=customer_data
                )

                if response.status_code == 201:
                    customer_id = response.json()["id"]
                    self.customers[key] = customer_id
                    logger.info(f"Created {key} with ID: {customer_id}")
                else:
                    logger.error(f"Failed to create {key}: {response.text}")
                    # Do not raise exception to continue with the demo
            except Exception as e:
                logger.error(f"Exception when creating {key}: {str(e)}")
                # Continue with the demo

        logger.info(f"Successfully created all customers: {self.customers}")

    def create_pricing_plans(self):
        """Create pricing plans for the API service."""
        logger.info("Creating pricing plans for API services...")

        # Basic API plan - simple tiered pricing
        basic_plan = {
            "name": "API Basic Plan",
            "description": "Basic API access with tiered pricing",
            "billing_frequency": "monthly",
            "price_components": [
                {
                    "metric_name": "api_calls",
                    "display_name": "API Calls",
                    "pricing_type": "tiered",
                    "pricing_details": {
                        "tiers": [
                            {"start": 0, "end": 1000, "price": 0.01},
                            {"start": 1000, "end": 10000, "price": 0.008},
                            {"start": 10000, "end": None, "price": 0.005},
                        ]
                    },
                },
                {
                    "metric_name": "data_transfer_gb",
                    "display_name": "Data Transfer (GB)",
                    "pricing_type": "volume",
                    "pricing_details": {
                        "tiers": [
                            {"start": 0, "end": 10, "price": 0.15},
                            {"start": 10, "end": 100, "price": 0.12},
                            {"start": 100, "end": None, "price": 0.10},
                        ]
                    },
                },
                {
                    "metric_name": "subscription_fee",
                    "display_name": "Basic Subscription Fee",
                    "pricing_type": "subscription",
                    "pricing_details": {"amount": 19.99},
                },
            ],
        }

        # Premium API plan - with additional features
        premium_plan = {
            "name": "API Premium Plan",
            "description": "Premium API access with advanced features",
            "billing_frequency": "monthly",
            "price_components": [
                {
                    "metric_name": "api_calls",
                    "display_name": "API Calls",
                    "pricing_type": "tiered",
                    "pricing_details": {
                        "tiers": [
                            {"start": 0, "end": 5000, "price": 0.008},
                            {"start": 5000, "end": 50000, "price": 0.006},
                            {"start": 50000, "end": None, "price": 0.004},
                        ]
                    },
                },
                {
                    "metric_name": "data_transfer_gb",
                    "display_name": "Data Transfer (GB)",
                    "pricing_type": "volume",
                    "pricing_details": {
                        "tiers": [
                            {"start": 0, "end": 50, "price": 0.12},
                            {"start": 50, "end": 500, "price": 0.09},
                            {"start": 500, "end": None, "price": 0.07},
                        ]
                    },
                },
                {
                    "metric_name": "compute_time_sec",
                    "display_name": "Compute Time (seconds)",
                    "pricing_type": "time_based",
                    "pricing_details": {"rate_per_unit": 0.00025, "unit": "second"},
                },
                {
                    "metric_name": "subscription_fee",
                    "display_name": "Premium Subscription Fee",
                    "pricing_type": "subscription",
                    "pricing_details": {"amount": 49.99},
                },
            ],
        }

        # Create the plans via API
        plans_to_create = {"basic_plan": basic_plan, "premium_plan": premium_plan}

        for key, plan_data in plans_to_create.items():
            logger.info(f"Creating plan: {plan_data['name']}")
            response = requests.post(f"{self.base_url}/plans/", json=plan_data)

            if response.status_code == 201:
                plan_id = response.json()["id"]
                self.plans[key] = plan_id
                logger.info(f"Created {key} with ID: {plan_id}")
            else:
                logger.error(f"Failed to create {key}: {response.text}")
                raise Exception(f"Failed to create plan {key}")

        logger.info(f"Successfully created all plans: {self.plans}")

    def create_subscriptions(self):
        """Create subscriptions for consumers to the API plans."""
        logger.info("Creating subscriptions for consumers...")

        # Current date for subscription start
        now = datetime.utcnow()
        start_date = (now - timedelta(days=30)).isoformat()

        # Consumer 1 subscribes to the Basic plan
        consumer1_subscription = {
            "plan_id": self.plans["basic_plan"],
            "start_date": start_date,
            "end_date": None,  # Ongoing subscription
        }

        # Consumer 2 subscribes to the Premium plan
        consumer2_subscription = {
            "plan_id": self.plans["premium_plan"],
            "start_date": start_date,
            "end_date": None,  # Ongoing subscription
        }

        # Create subscriptions via API
        subscriptions_to_create = {
            "consumer_1_basic": {
                "customer_id": self.customers["consumer_1"],
                "data": consumer1_subscription,
            },
            "consumer_2_premium": {
                "customer_id": self.customers["consumer_2"],
                "data": consumer2_subscription,
            },
        }

        for key, subscription_info in subscriptions_to_create.items():
            logger.info(f"Creating subscription: {key}")
            response = requests.post(
                f"{self.base_url}/customers/{subscription_info['customer_id']}/subscriptions",
                json=subscription_info["data"],
            )

            if response.status_code == 200:
                subscription_id = response.json()["id"]
                self.subscriptions[key] = subscription_id
                logger.info(f"Created {key} with ID: {subscription_id}")
            else:
                logger.error(f"Failed to create {key}: {response.text}")
                raise Exception(f"Failed to create subscription {key}")

        logger.info(f"Successfully created all subscriptions: {self.subscriptions}")

    def simulate_api_usage(self):
        """Simulate API usage events over a period of time."""
        logger.info("Simulating API usage events over the past 30 days...")

        # Set up simulation period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        current_date = start_date

        # Create random events throughout the period
        while current_date < end_date:
            # Simulate each day
            self.simulate_day_of_usage(current_date)
            current_date += timedelta(days=1)

        logger.info("Completed simulation of API usage events")

    def simulate_day_of_usage(self, day):
        """Simulate a single day of API usage."""
        logger.info(f"Simulating usage for {day.strftime('%Y-%m-%d')}...")

        # Consumer 1 (Basic Plan) - Lower volume
        # Generate 5-15 API call events throughout the day
        consumer1_events = random.randint(5, 15)
        for _ in range(consumer1_events):
            # Random time during the day
            event_time = day + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            # API calls - random number between 10-100 per event
            api_calls = random.randint(10, 100)
            self.record_event(
                self.customers["consumer_1"],
                "api_calls",
                api_calls,
                event_time,
                {
                    "endpoint": random.choice(
                        ["/users", "/products", "/orders", "/search"]
                    ),
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                },
            )

            # Data transfer - random between 0.1-2 GB
            data_transfer = round(random.uniform(0.1, 2.0), 2)
            self.record_event(
                self.customers["consumer_1"],
                "data_transfer_gb",
                data_transfer,
                event_time,
                {
                    "response_size": f"{data_transfer} GB",
                    "compression": random.choice(["gzip", "none"]),
                },
            )

        # Consumer 2 (Premium Plan) - Higher volume with more metrics
        # Generate 15-50 API call events throughout the day
        consumer2_events = random.randint(15, 50)
        for _ in range(consumer2_events):
            # Random time during the day
            event_time = day + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            # API calls - random number between 50-500 per event
            api_calls = random.randint(50, 500)
            self.record_event(
                self.customers["consumer_2"],
                "api_calls",
                api_calls,
                event_time,
                {
                    "endpoint": random.choice(
                        [
                            "/users",
                            "/products",
                            "/orders",
                            "/search",
                            "/analytics",
                            "/reports",
                        ]
                    ),
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                    "priority": random.choice(["high", "normal"]),
                },
            )

            # Data transfer - random between 0.5-10 GB
            data_transfer = round(random.uniform(0.5, 10.0), 2)
            self.record_event(
                self.customers["consumer_2"],
                "data_transfer_gb",
                data_transfer,
                event_time,
                {
                    "response_size": f"{data_transfer} GB",
                    "compression": random.choice(["gzip", "brotli", "none"]),
                    "cdn_used": random.choice([True, False]),
                },
            )

            # Compute time - random between 5-300 seconds
            compute_time = random.randint(5, 300)
            self.record_event(
                self.customers["consumer_2"],
                "compute_time_sec",
                compute_time,
                event_time,
                {
                    "job_type": random.choice(
                        ["data_processing", "report_generation", "ai_model_training"]
                    ),
                    "cpu_utilization": f"{random.randint(20, 95)}%",
                },
            )

    def record_event(
        self, customer_id, metric_name, quantity, event_time, properties=None
    ):
        """Record a usage event in Fubble."""
        event_data = {
            "customer_id": customer_id,
            "metric_name": metric_name,
            "quantity": quantity,
            "event_time": event_time.isoformat(),
            "properties": properties or {},
        }

        # Don't log every event to keep output manageable
        if random.random() < 0.05:  # Only log ~5% of events
            logger.info(
                f"Recording event: {metric_name} = {quantity} for customer {customer_id}"
            )

        response = requests.post(f"{self.base_url}/events/", json=event_data)

        if response.status_code != 201:
            logger.error(f"Failed to record event: {response.text}")
            logger.error(f"Event data: {event_data}")

    def generate_invoices(self):
        """Generate invoices for the simulation period."""
        logger.info("Generating invoices for the simulated usage period...")

        # Calculate invoice period (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Get usage summaries for each consumer
        self.display_usage_summary(self.customers["consumer_1"], start_date, end_date)
        self.display_usage_summary(self.customers["consumer_2"], start_date, end_date)

        # Generate invoices via API - send params as query parameters, not JSON body
        logger.info(
            f"Requesting invoice generation for period: {start_date.isoformat()} to {end_date.isoformat()}"
        )
        response = requests.post(
            f"{self.base_url}/invoices/generate",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "customer_id": self.customers["consumer_1"],
            },
        )

        if response.status_code == 200:
            invoices = response.json()
            logger.info(f"Successfully generated {len(invoices)} invoices")

            # Display invoice details
            for invoice in invoices:
                self.display_invoice(invoice)
        else:
            logger.error(f"Failed to generate invoices: {response.text}")

    def display_usage_summary(self, customer_id, start_date, end_date):
        """Display usage summary for a customer."""
        logger.info(f"Retrieving usage summary for customer {customer_id}...")

        response = requests.get(
            f"{self.base_url}/events/customers/{customer_id}/usage",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        if response.status_code == 200:
            usage_data = response.json()
            logger.info(f"Usage summary for customer {customer_id}:")
            for metric, quantity in usage_data.items():
                logger.info(f"  - {metric}: {quantity}")
        else:
            logger.error(f"Failed to retrieve usage summary: {response.text}")

    def display_invoice(self, invoice):
        """Display detailed invoice information."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"INVOICE: {invoice['invoice_number']}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Customer ID: {invoice['customer_id']}")
        logger.info(f"Status: {invoice['status']}")
        logger.info(f"Issue Date: {invoice['issue_date']}")
        logger.info(f"Due Date: {invoice['due_date']}")
        logger.info(f"Total Amount: ${invoice['amount']:.2f}")

        if invoice.get("notes"):
            logger.info(f"Notes: {invoice['notes']}")

        logger.info("\nINVOICE ITEMS:")
        logger.info(f"{'-' * 80}")
        logger.info(
            f"{'DESCRIPTION':<40} {'QUANTITY':<10} {'UNIT PRICE':<15} {'AMOUNT':<15}"
        )
        logger.info(f"{'-' * 80}")

        for item in invoice["invoice_items"]:
            quantity = item.get("quantity", "-")
            unit_price = f"${item['unit_price']:.4f}" if item["unit_price"] else "-"
            amount = f"${item['amount']:.2f}"

            logger.info(
                f"{item['description']:<40} "
                f"{quantity:<10} "
                f"{unit_price:<15} "
                f"{amount:<15}"
            )

        logger.info(f"{'-' * 80}")
        logger.info(f"{'TOTAL':<65} ${invoice['amount']:.2f}")
        logger.info(f"{'=' * 80}\n")


if __name__ == "__main__":
    # Run the demonstration
    demo = FubbleDemo()

    try:
        demo.run_demo()
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        import traceback

        logger.error(traceback.format_exc())
    else:
        logger.info("Demo completed successfully!")
