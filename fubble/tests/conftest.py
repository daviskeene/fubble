import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import uuid

from fubble.database.models import Base
from fubble.database.connection import get_db
from fubble.app import app


@pytest.fixture(scope="function")
def test_db_session():
    """Create a clean database session for testing."""
    # create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Create a session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        # Make sure to properly close the session
        db.close()
        # Dispose of the engine to close all connections
        engine.dispose()


@pytest.fixture
def override_get_db(test_db_session):
    """Override the get_db dependency for testing."""

    def _get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """Create a test client with the overridden database session."""
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture(scope="function")
def db(test_db_session):
    """Create a clean database session for each test."""
    # Start a nested transaction
    connection = test_db_session.connection()
    transaction = connection.begin_nested()

    try:
        yield test_db_session
    finally:
        # Roll back transaction to start of test
        transaction.rollback()
        # Expire all instances to ensure fresh state
        test_db_session.expire_all()
