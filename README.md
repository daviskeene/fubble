# FUBBLE: Flexible Usage Based Billing Lite Experiment

Code sample of how I would design a very simple usage-based billing engine.

## Overview

FUBBLE is a flexible, lightweight usage-based billing system designed to handle metered pricing models. It allows businesses to:

- Track customer usage across different metrics
- Apply tiered and complex pricing models
- Generate accurate invoices based on consumption
- Analyze billing data and usage patterns

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

1. Clone the repository
```bash
git clone https://github.com/daviskeene/fubble.git
cd fubble
```

2. Install dependencies
```bash
python3 -m pip install -r requirements.txt
```

3. Install the package in development mode
```bash
python3 -m pip install -e .
```

4. Set up the database
```bash
python3 -m fubble.database.setup
```

5. Run the application
```bash
python3 -m fubble.app
```

## Usage Examples

FUBBLE provides a flexible framework for implementing usage-based billing in your application. Here's how you can use it:

### 1. Define Your Pricing Plans

Create pricing plans with different components and billing models:

```python
# Example: tiered api pricing
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
            }
        },
        # Additional price components...
    ]
}

# Create the plan
response = requests.post("http://localhost:8000/plans/", json=basic_plan)
```

### 2. Register Customers

Add customers to your billing system:

```python
customer = {
    "name": "Company A",
    "email": "billing@companya.com",
    "company_name": "Company A Inc.",
    "billing_address": "123 Tech Park, San Francisco, CA 94105",
    "payment_method_id": "pm_card_visa"
}

response = requests.post("http://localhost:8000/customers/", json=customer)
customer_id = response.json()["id"]
```

### 3. Create Subscriptions

Subscribe customers to your plans:

```python
subscription = {
    "plan_id": plan_id,
    "start_date": datetime.utcnow().isoformat(),
    "end_date": None  # Ongoing subscription
}

response = requests.post(
    f"http://localhost:8000/customers/{customer_id}/subscriptions",
    json=subscription
)
```

### 4. Record Usage Events

Track customer usage with detailed event data:

```python
event_data = {
    "customer_id": customer_id,
    "metric_name": "api_calls",
    "quantity": 50,
    "event_time": datetime.utcnow().isoformat(),
    "properties": {
        "endpoint": "/users",
        "method": "GET"
    }
}

# events are the building block of all invoices and billing statements
response = requests.post("http://localhost:8000/events/", json=event_data)
```

### 5. Generate Invoices

Create invoices based on the recorded usage:

```python
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)

response = requests.post(
    "http://localhost:8000/invoices/generate",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
)

invoices = response.json()
```

For a complete demonstration, see the included `demo.py` script.

```
python3 demo.py
```

## How I Used AI

Throughout the development of FUBBLE, I leveraged AI assistance in several key areas:

- Creating comprehensive docstrings for classes and methods
- Generating unit tests based on desired functionality
- Large, low-entropy code refactors

The goal was to use AI as a collaborative tool while maintaining control over the architecture and critical design decisions. All AI-generated code was reviewed and often modified to ensure it met the project's quality standards and design principles.

## Trade-Offs

In designing FUBBLE, I made several intentional trade-offs to balance simplicity, flexibility, and time constraints:

### API Design
- I chose SQLite for data storage instead of an event streaming platform like Apache Kafka
- The web server implementation is straightforward and not designed for distributed deployment. In a production environment, you'd want to implement load balancing and redundancy.
- The current API doesn't implement authentication or authorization. In a production setting, you'd need to add proper security controls.
- Events are processed synchronously rather than using a queue-based approach, which would lead to performance bottlenecks at scale.

### System Architecture
- The system uses a flexible schema for usage events, allowing for dynamic properties. This provides great adaptability but may lead to data consistency challenges.
- Usage calculations happen in-memory, which works well for moderate data volumes but wouldn't scale to extremely high volumes of usage data.
- While the system supports multiple pricing models, it doesn't implement more complex scenarios like cross-metric volume discounts or negotiated enterprise pricing.
- The system focuses on invoice generation and doesn't include payment processing or integration with payment gateways.
- While the system tracks comprehensive usage data, it lacks advanced analytics and reporting capabilities.

These trade-offs were made intentionally to create a lightweight, functional system that demonstrates the core concepts of usage-based billing without unnecessary complexity.

## Testing

Run tests with pytest:
```bash
pytest
```