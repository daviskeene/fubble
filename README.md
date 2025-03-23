# FUBBLE: Flexible Usage Based Billing Lite Experiment

Code sample of how I would design a very simple usage-based billing engine.

## Overview

FUBBLE is a flexible, lightweight usage-based billing system designed to handle metered pricing models. It allows businesses to:

- Track customer usage across different metrics
- Apply tiered and complex pricing models
- Generate accurate invoices based on consumption
- Analyze billing data and usage patterns

## Architecture

```
fubble/
├── api/                  # FastAPI endpoints for the service
│   ├── __init__.py
│   ├── customers.py      # Customer management endpoints
│   ├── events.py         # Usage event tracking endpoints
│   ├── invoices.py       # Invoice generation endpoints
│   └── plans.py          # Pricing plan endpoints
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── billing.py        # Billing calculation engine
│   ├── customers.py      # Customer management
│   ├── events.py         # Usage event processing
│   ├── invoices.py       # Invoice generation
│   └── plans.py          # Pricing plan management
├── database/             # Database models and connections
│   ├── __init__.py
│   ├── models.py         # SQLAlchemy models
│   └── connection.py     # Database connection management
├── services/             # External service integrations
│   ├── __init__.py
│   ├── analytics.py      # Analytics service
│   └── payment.py        # Payment processing
├── utils/                # Utility functions
│   ├── __init__.py
│   └── helpers.py        # Common helper functions
├── tests/                # Unit and integration tests
│   ├── __init__.py
│   ├── test_billing.py
│   ├── test_customers.py
│   └── test_events.py
├── app.py                # Application entry point
├── config.py             # Configuration management
├── requirements.txt      # Project dependencies
└── README.md             # Documentation
```

## Key Concepts

1. **Customers**: Organizations or individuals who subscribe to services
2. **Plans**: Pricing models that define how usage is billed
3. **Usage Events**: Records of service consumption
4. **Billing Period**: Timeframe for calculating charges
5. **Invoices**: Itemized bills generated for customers

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL (or SQLite for development)

### Installation

1. Clone the repository
```bash
git clone https://github.com/daviskeene/fubble.git
cd fubble
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Install the package in development mode
```bash
pip install -e .
```

5. Set up the database
```bash
python -m fubble.database.setup
```

6. Run the application
```bash
python -m fubble.app
```

## Usage Examples

See the documentation in the `/examples` directory for detailed usage examples.

## Testing

Run tests with pytest:
```bash
pytest
```