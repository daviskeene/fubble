import logging
from sqlalchemy_utils import database_exists, create_database

from fubble.database.connection import engine, Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """
    Set up the database by creating all tables if they don't exist.
    """
    logger.info("Setting up database...")

    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        logger.info(f"Created database at {engine.url}")

    # Create all tables
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def teardown_database():
    """
    Tear down the database by dropping all tables.
    This will typically be used for testing.
    """
    logger.info("Tearing down database...")

    # Drop all tables
    Base.metadata.drop_all(engine)
    logger.info("Database tables dropped successfully")


if __name__ == "__main__":
    setup_database()
