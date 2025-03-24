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