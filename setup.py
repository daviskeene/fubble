from setuptools import setup, find_packages

setup(
    name="fubble",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "sqlalchemy-utils",
        "alembic",
        "psycopg2-binary",
        "pydantic",
        "pydantic-settings",
        "python-jose",
        "passlib",
        "python-dateutil",
        "pendulum",
        "email-validator",
    ],
)
