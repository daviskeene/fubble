from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BillingFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PricingType(str, Enum):
    FLAT = "flat"
    TIERED = "tiered"
    VOLUME = "volume"
    PACKAGE = "package"
    GRADUATED = "graduated"
    THRESHOLD = "threshold"
    SUBSCRIPTION = "subscription"
    USAGE_BASED_SUBSCRIPTION = "usage_based_subscription"
    DYNAMIC = "dynamic"
    TIME_BASED = "time_based"
    DIMENSION_BASED = "dimension_based"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    VOID = "void"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    company_name = Column(String(255))
    billing_address = Column(Text)
    payment_method_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    usage_events = relationship("UsageEvent", back_populates="customer")
    customer_features = relationship("CustomerFeature", back_populates="customer")
    credit_balances = relationship("CreditBalance", back_populates="customer")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    billing_frequency = Column(SQLAEnum(BillingFrequency), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    price_components = relationship("PriceComponent", back_populates="plan")
    subscriptions = relationship("Subscription", back_populates="plan")
    plan_features = relationship("PlanFeature", back_populates="plan")


class PriceComponent(Base):
    __tablename__ = "price_components"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)  # e.g., "api_calls", "storage_gb"
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=True)
    display_name = Column(String(255), nullable=False)
    pricing_type = Column(SQLAEnum(PricingType), nullable=False)
    pricing_details = Column(
        JSON, nullable=False
    )  # Holds tier information, rates, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan = relationship("Plan", back_populates="price_components")
    metric = relationship("Metric", back_populates="price_components")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # Null means ongoing
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    billing_periods = relationship("BillingPeriod", back_populates="subscription")
    commitment_tiers = relationship("CommitmentTier", back_populates="subscription")
    credit_balances = relationship("CreditBalance", back_populates="subscription")


class BillingPeriod(Base):
    __tablename__ = "billing_periods"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="billing_periods")
    invoice = relationship("Invoice", back_populates="billing_periods")
    usage_events = relationship("UsageEvent", back_populates="billing_period")


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    billing_period_id = Column(Integer, ForeignKey("billing_periods.id"), nullable=True)
    metric_name = Column(String(255), nullable=False)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=True)
    quantity = Column(Float, nullable=False)
    event_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    properties = Column(JSON)  # Additional data about the event
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="usage_events")
    subscription = relationship("Subscription", backref="usage_events")
    billing_period = relationship("BillingPeriod", back_populates="usage_events")
    metric = relationship("Metric", back_populates="usage_events")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False, unique=True)
    status = Column(SQLAEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    paid_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")
    billing_periods = relationship("BillingPeriod", back_populates="invoice")
    credit_balances = relationship("CreditBalance", back_populates="invoice")
    credit_transactions = relationship("CreditTransaction", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    metric_name = Column(String(255))
    quantity = Column(Float)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")
    subscription = relationship("Subscription", backref="invoice_items")


class MetricType(str, Enum):
    COUNTER = "counter"  # Always increases (e.g., API calls, messages sent)
    GAUGE = "gauge"  # Can go up and down (e.g., storage usage)
    DIMENSION = "dimension"  # Has additional attributes (e.g., compute with CPU/memory)
    TIME = "time"  # Duration-based metrics (e.g., active minutes)
    COMPOSITE = "composite"  # Derived from other metrics


class AggregationType(str, Enum):
    SUM = "sum"  # Add up all values in period
    MAX = "max"  # Take maximum value in period
    MIN = "min"  # Take minimum value in period
    AVG = "avg"  # Average value over period
    LAST = "last"  # Last value in period
    PERCENTILE = "percentile"  # Nth percentile of values


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    unit = Column(String(50))  # e.g., MB, API calls, messages
    type = Column(SQLAEnum(MetricType), nullable=False)
    aggregation_type = Column(SQLAEnum(AggregationType), nullable=False, default="sum")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # If this is a composite metric, store the formula as a JSON expression
    formula = Column(JSON)

    # Default properties for display purposes (e.g., decimals to show)
    display_properties = Column(JSON)

    # Relationships
    price_components = relationship("PriceComponent", back_populates="metric")
    usage_events = relationship("UsageEvent", back_populates="metric")
    commitment_tiers = relationship("CommitmentTier", back_populates="metric")


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan_features = relationship("PlanFeature", back_populates="feature")
    customer_features = relationship("CustomerFeature", back_populates="feature")


class PlanFeature(Base):
    __tablename__ = "plan_features"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    limits = Column(JSON)  # Optional limits for this feature (e.g., max_users: 5)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    plan = relationship("Plan", back_populates="plan_features")
    feature = relationship("Feature", back_populates="plan_features")


class CustomerFeature(Base):
    __tablename__ = "customer_features"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    override_limits = Column(JSON)  # Override default limits from plan
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="customer_features")
    feature = relationship("Feature", back_populates="customer_features")


class CreditType(str, Enum):
    PREPAID = "prepaid"
    REFUND = "refund"
    PROMOTIONAL = "promotional"
    ADJUSTMENT = "adjustment"


class CreditStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    credit_type = Column(SQLAEnum(CreditType), nullable=False)
    status = Column(SQLAEnum(CreditStatus), nullable=False, default="active")
    expires_at = Column(DateTime)  # Optional expiration date
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(Text)

    # Optional associations
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    # Relationships
    customer = relationship("Customer", back_populates="credit_balances")
    invoice = relationship("Invoice", back_populates="credit_balances")
    subscription = relationship("Subscription", back_populates="credit_balances")
    credit_transactions = relationship(
        "CreditTransaction", back_populates="credit_balance"
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    credit_balance_id = Column(
        Integer, ForeignKey("credit_balances.id"), nullable=False
    )
    amount = Column(Float, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional association with invoice
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    # Relationships
    credit_balance = relationship("CreditBalance", back_populates="credit_transactions")
    invoice = relationship("Invoice", back_populates="credit_transactions")


class CommitmentTier(Base):
    __tablename__ = "commitment_tiers"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False)
    committed_amount = Column(Float, nullable=False)
    rate = Column(Float, nullable=False)  # Price per unit for committed amount
    overage_rate = Column(Float)  # Optional different rate for usage above commitment
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # Null means no end date
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="commitment_tiers")
    metric = relationship("Metric", back_populates="commitment_tiers")
