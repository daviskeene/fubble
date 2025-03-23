import pytest
from sqlalchemy import inspect
from fubble.database.models import Base, UsageEvent


def test_database_schema(test_db_session):
    """Test to debug database schema issues"""
    # Get raw connection
    inspector = inspect(test_db_session.bind)

    # Print all tables
    tables = inspector.get_table_names()
    print(f"\nTables in database: {tables}")

    # Print schema for usage_events
    usage_columns = inspector.get_columns("usage_events")
    print(f"\nColumns in usage_events: {[col['name'] for col in usage_columns]}")

    # Print model attributes
    model_attrs = [attr for attr in dir(UsageEvent) if not attr.startswith("_")]
    print(f"\nUsageEvent model attributes: {model_attrs}")

    # Print table metadata from SQLAlchemy model
    table_columns = [c.name for c in UsageEvent.__table__.columns]
    print(f"\nUsageEvent.__table__.columns: {table_columns}")

    # Check if there are multiple Base definitions
    table_columns_from_base = [
        c.name for c in Base.metadata.tables["usage_events"].columns
    ]
    print(f"\nBase.metadata columns for usage_events: {table_columns_from_base}")

    # Verify metric_id exists in table
    assert "metric_id" in [
        col["name"] for col in usage_columns
    ], "metric_id not found in actual database table"
    assert "metric_id" in table_columns, "metric_id not found in model's __table__"
    assert (
        "metric_id" in table_columns_from_base
    ), "metric_id not found in Base.metadata"
