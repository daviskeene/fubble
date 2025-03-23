from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

from sqlalchemy.orm import Session

from fubble.database.models import (
    BillingPeriod,
    Customer,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Plan,
    PriceComponent,
    PricingType,
    Subscription,
    UsageEvent,
    Metric,
    CommitmentTier,
    CreditBalance,
    CreditStatus,
    CreditTransaction,
)
from fubble.config import settings


class BillingEngine:
    """
    Core billing calculation engine responsible for calculating usage-based charges
    and generating invoices based on customer usage and pricing plans.
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger("fubble-billing")

    def calculate_usage_for_date_range(
        self, customer_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculates total usage for each metric in a date range for a specific customer.

        Args:
            customer_id: The ID of the customer to calculate usage for.
            start_date: The start date of the period.
            end_date: The end date of the period.

        Returns:
            A dictionary mapping metric names to their total usage quantity.
        """
        # Modified query to handle both subscription-based and direct usage events
        usage_events_query = self.db.query(UsageEvent).filter(
            UsageEvent.customer_id == customer_id,
            UsageEvent.event_time >= start_date,
            UsageEvent.event_time <= end_date,
        )

        # Execute query
        usage_events = usage_events_query.all()

        # Aggregate usage by metric
        usage_by_metric = {}
        for event in usage_events:
            if event.metric_name not in usage_by_metric:
                usage_by_metric[event.metric_name] = 0
            usage_by_metric[event.metric_name] += event.quantity

        self.logger.info(
            f"Calculated usage for customer {customer_id} from {start_date} to {end_date}: {usage_by_metric}"
        )
        return usage_by_metric

    def calculate_usage_for_billing_period(
        self, billing_period: BillingPeriod
    ) -> Dict[str, float]:
        """
        Calculates total usage for each metric in a billing period.

        Args:
            billing_period: The billing period to calculate usage for.

        Returns:
            A dictionary mapping metric names to their total usage quantity.
        """
        # Get the customer ID from the subscription
        customer_id = billing_period.subscription.customer_id

        # Delegate to the date range method
        return self.calculate_usage_for_date_range(
            customer_id=customer_id,
            start_date=billing_period.start_date,
            end_date=billing_period.end_date,
        )

    def calculate_charge_for_component(
        self, component: PriceComponent, usage_quantity: float
    ) -> Tuple[float, float, str]:
        """
        Calculates the charge for a specific price component based on usage.

        Args:
            component: The price component to calculate charges for.
            usage_quantity: The quantity of usage for this component.

        Returns:
            A tuple containing (total_charge, unit_price, description)
        """
        pricing_details = component.pricing_details

        self.logger.info(
            f"Calculating charge for {component.metric_name} with usage_quantity={usage_quantity}"
        )
        self.logger.info(
            f"Pricing type: {component.pricing_type}, Pricing details: {pricing_details}"
        )

        if component.pricing_type == PricingType.FLAT:
            # Flat fee is independent of usage
            return (
                pricing_details["amount"],
                pricing_details["amount"],
                f"Flat fee for {component.display_name}",
            )

        elif component.pricing_type == PricingType.TIERED:
            # Tiered pricing calculates different rates for different usage ranges
            tiers = pricing_details["tiers"]
            total_charge = 0
            tier_charges = []

            remaining_usage = usage_quantity
            effective_unit_price = 0

            for tier in tiers:
                tier_start = tier.get("start", 0)
                tier_end = tier.get("end")  # Can be None for unlimited
                tier_price = tier["price"]

                # Skip tiers that don't apply
                if tier_end is not None and tier_start > usage_quantity:
                    continue

                # Calculate usage in this tier
                if tier_end is None:
                    # Unlimited tier
                    tier_usage = remaining_usage
                else:
                    tier_usage = min(remaining_usage, tier_end - tier_start)

                tier_charge = tier_usage * tier_price
                total_charge += tier_charge
                tier_charges.append(
                    f"{tier_usage} units @ ${tier_price}/unit = ${tier_charge}"
                )

                remaining_usage -= tier_usage
                if remaining_usage <= 0:
                    break

            # Calculate effective unit price (total / usage)
            if usage_quantity > 0:
                effective_unit_price = total_charge / usage_quantity

            description = f"Tiered pricing for {component.display_name}: " + ", ".join(
                tier_charges
            )
            return (total_charge, effective_unit_price, description)

        elif component.pricing_type == PricingType.VOLUME:
            # Volume pricing applies a single rate based on total volume
            tiers = pricing_details["tiers"]
            applied_tier = None

            # Find applicable tier
            for tier in reversed(tiers):  # Start from highest tier
                tier_start = tier.get("start", 0)
                if usage_quantity >= tier_start:
                    applied_tier = tier
                    break

            if applied_tier is None:
                # Fallback to first tier
                applied_tier = tiers[0]

            price = applied_tier["price"]
            total_charge = usage_quantity * price

            description = f"Volume pricing for {component.display_name}: {usage_quantity} units @ ${price}/unit"
            return (total_charge, price, description)

        elif component.pricing_type == PricingType.PACKAGE:
            # Package pricing sells units in predefined packages (e.g., 1000 API calls)
            package_size = pricing_details["package_size"]
            package_price = pricing_details["package_price"]

            # Calculate number of packages (round up)
            num_packages = (usage_quantity + package_size - 1) // package_size

            total_charge = num_packages * package_price
            effective_unit_price = (
                total_charge / usage_quantity if usage_quantity > 0 else 0
            )

            description = f"Package pricing for {component.display_name}: {num_packages} packages of {package_size} units @ ${package_price}/package"
            return (total_charge, effective_unit_price, description)

        elif component.pricing_type == PricingType.GRADUATED:
            # Graduated pricing is like tiered but without marginal pricing
            # Each tier applies to the entire usage once a threshold is reached
            tiers = pricing_details["tiers"]
            applied_tier = None

            # Find applicable tier
            for tier in reversed(tiers):  # Start from highest tier
                tier_start = tier.get("start", 0)
                if usage_quantity >= tier_start:
                    applied_tier = tier
                    break

            if applied_tier is None:
                # Fallback to first tier
                applied_tier = tiers[0]

            price = applied_tier["price"]
            total_charge = usage_quantity * price

            description = f"Graduated pricing for {component.display_name}: {usage_quantity} units @ ${price}/unit (tier: {applied_tier['start']}+)"
            return (total_charge, price, description)

        elif component.pricing_type == PricingType.THRESHOLD:
            # Threshold pricing charges a fixed amount once usage crosses a threshold
            thresholds = pricing_details["thresholds"]
            total_charge = 0
            threshold_charges = []

            for threshold in thresholds:
                threshold_value = threshold["threshold"]
                threshold_price = threshold["price"]

                if usage_quantity >= threshold_value:
                    total_charge += threshold_price
                    threshold_charges.append(
                        f"Threshold {threshold_value} crossed: ${threshold_price}"
                    )

            effective_unit_price = (
                total_charge / usage_quantity if usage_quantity > 0 else 0
            )
            description = (
                f"Threshold pricing for {component.display_name}: "
                + ", ".join(threshold_charges)
            )
            return (total_charge, effective_unit_price, description)

        elif component.pricing_type == PricingType.SUBSCRIPTION:
            # Subscription pricing is just a recurring flat fee
            amount = pricing_details["amount"]
            return (amount, amount, f"Subscription fee for {component.display_name}")

        elif component.pricing_type == PricingType.USAGE_BASED_SUBSCRIPTION:
            # Base fee plus usage charges
            base_fee = pricing_details.get("base_fee", 0)
            usage_price = pricing_details.get("usage_price", 0)

            usage_charge = usage_quantity * usage_price
            total_charge = base_fee + usage_charge

            effective_unit_price = (
                total_charge / usage_quantity if usage_quantity > 0 else base_fee
            )

            description = f"Usage-based subscription for {component.display_name}: ${base_fee} base + {usage_quantity} units @ ${usage_price}/unit = ${total_charge}"
            return (total_charge, effective_unit_price, description)

        elif component.pricing_type == PricingType.TIME_BASED:
            # Time-based pricing based on duration
            rate_per_unit = pricing_details.get("rate_per_unit", 0)
            unit = pricing_details.get("unit", "hour")  # hour, minute, second, etc.

            total_charge = usage_quantity * rate_per_unit

            description = f"Time-based pricing for {component.display_name}: {usage_quantity} {unit}s @ ${rate_per_unit}/{unit}"
            return (total_charge, rate_per_unit, description)

        elif component.pricing_type == PricingType.DIMENSION_BASED:
            # Dimension-based pricing with multiple factors
            dimensions = pricing_details.get("dimensions", {})
            base_rate = pricing_details.get("base_rate", 0)

            # Collect dimensions from the usage event's properties
            # This would typically come from the usage_event.properties JSON field
            # dimension_values = usage_event.properties.get("dimensions", {})

            total_rate = base_rate
            dimension_factors = []  # Initialize the list
            for dimension_name, dimension_config in dimensions.items():
                dimension_value = dimension_config.get(dimension_name, 0)
                dimension_multiplier = dimension_config.get("multiplier", 1)
                dimension_factor = dimension_value * dimension_multiplier

                total_rate *= 1 + dimension_factor
                dimension_factors.append(
                    f"{dimension_name}: {dimension_value} (factor: {dimension_factor:.2f})"
                )

            total_charge = usage_quantity * total_rate

            factor_desc = (
                ", ".join(dimension_factors)
                if dimension_factors
                else "no dimension adjustments"
            )
            description = f"Dimension-based pricing for {component.display_name}: {usage_quantity} units @ ${total_rate}/unit ({factor_desc})"
            return (total_charge, total_rate, description)

        elif component.pricing_type == PricingType.DYNAMIC:
            # Dynamic pricing based on a formula or external API
            # This is just a placeholder - in a real implementation,
            # you would define formula parsing logic or API calls
            formula = pricing_details.get("formula", "")
            base_rate = pricing_details.get("base_rate", 0)

            # Dummy implementation - in reality, you'd evaluate the formula
            total_rate = base_rate
            total_charge = usage_quantity * total_rate

            description = f"Dynamic pricing for {component.display_name}: {usage_quantity} units @ ${total_rate}/unit (formula: {formula})"
            return (total_charge, total_rate, description)

        # Unknown pricing type
        return (0, 0, f"Unknown pricing type for {component.display_name}")

    def generate_invoice_for_date_range(
        self,
        customer_id: int,
        start_date: datetime,
        end_date: datetime,
        subscription_id: Optional[int] = None,
    ) -> Invoice:
        """
        Generates an invoice for a customer based on usage within a date range.

        Args:
            customer_id: The ID of the customer.
            start_date: The start date of the period.
            end_date: The end date of the period.
            subscription_id: Optional subscription ID to associate with this invoice.

        Returns:
            The created invoice object.
        """
        # Get the customer
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")

        self.logger.info(
            f"Generating invoice for customer {customer_id} from {start_date} to {end_date}"
        )

        # Get active subscriptions for this customer during this period
        subscriptions = []
        if subscription_id:
            # If specific subscription provided, use just that one
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.id == subscription_id)
                .first()
            )
            if subscription:
                subscriptions = [subscription]
        else:
            # Otherwise, find all active subscriptions during this period
            subscriptions = (
                self.db.query(Subscription)
                .filter(
                    Subscription.customer_id == customer_id,
                    Subscription.start_date <= end_date,
                    (
                        Subscription.end_date.is_(None)
                        | (Subscription.end_date >= start_date)
                    ),
                )
                .all()
            )

        if not subscriptions:
            self.logger.warning(
                f"No active subscriptions found for customer {customer_id} during period"
            )

        # Get usage for the date range
        usage_by_metric = self.calculate_usage_for_date_range(
            customer_id, start_date, end_date
        )
        self.logger.info(f"Usage data for date range: {usage_by_metric}")

        # Create invoice with a unique invoice number
        current_time = datetime.utcnow()
        time_str = current_time.strftime('%Y%m%d%H%M%S')  # Add hours, minutes, seconds for uniqueness
        
        invoice = Invoice(
            customer_id=customer_id,
            invoice_number=f"INV-{time_str}-{customer_id}-{start_date.strftime('%Y%m%d')}",
            status=InvoiceStatus.DRAFT,
            issue_date=current_time,
            due_date=current_time + timedelta(days=settings.DEFAULT_PAYMENT_TERM_DAYS),
            amount=0,  # Will be updated after calculating line items
            notes=f"Invoice for usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        )

        self.db.add(invoice)
        self.db.flush()  # Get invoice ID

        # Create invoice items
        total_amount = 0

        # Process each subscription
        for subscription in subscriptions:
            plan = subscription.plan

            # Handle subscription base charges (if applicable)
            if (
                subscription_id
            ):  # Only add subscription fees if this is for a specific subscription
                for component in plan.price_components:
                    if component.pricing_type in [
                        PricingType.FLAT,
                        PricingType.SUBSCRIPTION,
                    ]:
                        # Flat fees and subscription charges don't depend on usage
                        (
                            charge,
                            unit_price,
                            description,
                        ) = self.calculate_charge_for_component(
                            component, 1  # Quantity is 1 for subscription/flat fees
                        )

                        # Create invoice item for the subscription fee
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            description=description,
                            metric_name=component.metric_name,
                            quantity=1,
                            unit_price=unit_price,
                            amount=charge,
                            subscription_id=subscription.id,
                        )

                        self.db.add(invoice_item)
                        total_amount += charge

            # Handle minimum commitments if applicable
            commitment_charges = {}
            if (
                subscription_id
            ):  # Only apply commitments for specific subscription invoices
                commitment_charges = self._calculate_commitment_charges_for_date_range(
                    subscription, start_date, end_date, usage_by_metric
                )
                self.logger.info(
                    f"Commitment charges for subscription {subscription.id}: {commitment_charges}"
                )

            # Process usage-based charges for this subscription's plan
            price_components = plan.price_components
            for component in price_components:
                # Skip non-usage components if we already handled them
                if (
                    component.pricing_type
                    in [PricingType.FLAT, PricingType.SUBSCRIPTION]
                    and subscription_id
                ):
                    continue

                usage_quantity = usage_by_metric.get(component.metric_name, 0)
                self.logger.info(
                    f"Processing component: {component.metric_name}, usage: {usage_quantity}"
                )

                charge, unit_price, description = self.calculate_charge_for_component(
                    component, usage_quantity
                )

                self.logger.info(
                    f"Calculated: charge={charge}, unit_price={unit_price}, description={description}"
                )

                # Check if this metric has a commitment that's already fulfilled
                if component.metric_id and subscription_id:
                    metric_id = component.metric_id
                    commitment_charge = commitment_charges.get(metric_id, 0)
                    if commitment_charge > 0:
                        # If there's a commitment charge, use that instead of normal pricing
                        # but only if it's greater (enforce minimum charge)
                        if commitment_charge > charge:
                            self.logger.info(
                                f"Using commitment charge {commitment_charge} instead of calculated charge {charge}"
                            )
                            charge = commitment_charge
                            description = f"Minimum commitment for {component.display_name}: ${charge}"

                        # Remove this metric from commitment charges since it's been applied
                        commitment_charges.pop(metric_id, None)
                # Create invoice item for usage-based charge
                if charge > 0 or usage_quantity > 0:
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=description,
                        metric_name=component.metric_name,
                        quantity=usage_quantity,
                        unit_price=unit_price,
                        amount=charge,
                        subscription_id=subscription.id,
                    )

                    self.db.add(invoice_item)
                    total_amount += charge

            # Add any remaining commitment charges as separate line items
            if subscription_id:
                for metric_id, charge in commitment_charges.items():
                    metric = (
                        self.db.query(Metric).filter(Metric.id == metric_id).first()
                    )
                    if metric and charge > 0:
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            description=f"Minimum commitment for {metric.display_name}",
                            metric_name=metric.name,
                            quantity=0,  # No usage, just commitment
                            unit_price=0,
                            amount=charge,
                            subscription_id=subscription.id,
                        )

                        self.db.add(invoice_item)
                        total_amount += charge

        # Update invoice total
        invoice.amount = total_amount

        # Apply credits to the invoice if available
        final_amount = self._apply_credits_to_invoice(invoice, customer, total_amount)
        invoice.amount = final_amount

        self.db.commit()
        return invoice

    def generate_invoice(self, billing_period: BillingPeriod) -> Invoice:
        """
        Generates an invoice for a subscription's billing period.
        
        A billing period is tied to a specific subscription, so this method generates
        an invoice that includes subscription fees, any usage-based charges for the period,
        and ensures all subscription-specific pricing rules (like commitments) are applied.

        Args:
            billing_period: The billing period to generate an invoice for.

        Returns:
            The created invoice object.
        """
        subscription = billing_period.subscription
        customer = subscription.customer
        plan = subscription.plan

        self.logger.info(
            f"Generating invoice for billing period {billing_period.id} "
            f"of subscription {subscription.id} (Plan: {plan.name}) "
            f"for customer {customer.id} from {billing_period.start_date} to {billing_period.end_date}"
        )

        # Calculate usage for this billing period
        usage_by_metric = self.calculate_usage_for_billing_period(billing_period)
        self.logger.info(f"Usage data for billing period {billing_period.id}: {usage_by_metric}")
        
        # Generate the invoice using the core functionality
        # We're passing the subscription_id which ensures all subscription-specific
        # pricing rules (like commitments and subscription fees) will be applied
        invoice = self.generate_invoice_for_date_range(
            customer_id=customer.id,
            start_date=billing_period.start_date,
            end_date=billing_period.end_date,
            subscription_id=subscription.id,
        )
        
        # Enhance the invoice notes to clearly indicate this is for a billing period
        invoice.notes = f"Invoice for subscription {subscription.id} ({plan.name}) - " \
                        f"Billing period: {billing_period.start_date.strftime('%Y-%m-%d')} to {billing_period.end_date.strftime('%Y-%m-%d')}"
        
        # Link billing period to invoice
        billing_period.invoice_id = invoice.id
        self.db.commit()
        
        self.logger.info(f"Generated invoice {invoice.id} for billing period {billing_period.id}")
        return invoice

    def _calculate_commitment_charges_for_date_range(
        self, subscription, start_date, end_date, usage_by_metric
    ):
        """
        Calculate charges based on minimum commitments for a subscription within a date range.

        Args:
            subscription: The subscription to check for commitments.
            start_date: The start date of the period.
            end_date: The end date of the period.
            usage_by_metric: Current usage by metric.

        Returns:
            Dictionary mapping metric_ids to minimum commitment charges.
        """
        commitment_charges = {}

        # Get active commitment tiers for this subscription and date range
        commitment_tiers = (
            self.db.query(CommitmentTier)
            .filter(
                CommitmentTier.subscription_id == subscription.id,
                CommitmentTier.start_date <= end_date,
                (
                    CommitmentTier.end_date.is_(None)
                    | (CommitmentTier.end_date >= start_date)
                ),
            )
            .all()
        )

        # Calculate commitment charges (same logic as before)
        for commitment in commitment_tiers:
            metric = commitment.metric
            metric_name = metric.name
            committed_amount = commitment.committed_amount
            rate = commitment.rate

            # Get actual usage
            actual_usage = usage_by_metric.get(metric_name, 0)

            # Calculate expected charge for commitment
            committed_charge = committed_amount * rate

            # Calculate actual charge
            actual_charge = 0
            if actual_usage > 0:
                if (
                    commitment.overage_rate is not None
                    and actual_usage > committed_amount
                ):
                    # Base charge for committed amount
                    actual_charge = committed_amount * rate
                    # Add overage
                    overage = actual_usage - committed_amount
                    actual_charge += overage * commitment.overage_rate
                else:
                    # Regular rate for all usage
                    actual_charge = actual_usage * rate

            # If committed charge is greater, that's the minimum
            if committed_charge > actual_charge:
                commitment_charges[metric.id] = committed_charge

        return commitment_charges

    def _apply_credits_to_invoice(self, invoice, customer, total_amount):
        """
        Apply available credits to an invoice.

        Args:
            invoice: The invoice to apply credits to.
            customer: The customer who owns the credits.
            total_amount: The total invoice amount before credits.

        Returns:
            The final invoice amount after applying credits.
        """
        # Get active credits for this customer, ordered by expiration date (soonest first)
        active_credits = (
            self.db.query(CreditBalance)
            .filter(
                CreditBalance.customer_id == customer.id,
                CreditBalance.status == CreditStatus.ACTIVE,
                CreditBalance.remaining_amount > 0,
            )
            .order_by(CreditBalance.expires_at.asc())
            .all()
        )

        remaining_invoice_amount = total_amount

        for credit in active_credits:
            if remaining_invoice_amount <= 0:
                break

            # Determine amount to apply from this credit
            amount_to_apply = min(credit.remaining_amount, remaining_invoice_amount)

            if amount_to_apply <= 0:
                continue

            # Update credit balance
            credit.remaining_amount -= amount_to_apply
            if credit.remaining_amount <= 0:
                credit.status = CreditStatus.CONSUMED

            # Create transaction record
            transaction = CreditTransaction(
                credit_balance_id=credit.id,
                amount=-amount_to_apply,  # Negative because it's a deduction
                description=f"Applied to invoice {invoice.invoice_number}",
                invoice_id=invoice.id,
            )

            self.db.add(transaction)

            # Update remaining invoice amount
            remaining_invoice_amount -= amount_to_apply

            # Add credit application line item to invoice
            credit_item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"Credit applied: {credit.description or 'Credit balance'}",
                metric_name=None,
                quantity=1,
                unit_price=-amount_to_apply,
                amount=-amount_to_apply,  # Negative because it reduces the total
            )

            self.db.add(credit_item)

        return max(0, remaining_invoice_amount)

    def generate_invoices_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_id: Optional[int] = None,
    ) -> List[Invoice]:
        """
        Generates invoices for all billing periods or directly by date range within a date range.

        Args:
            start_date: The start date for the invoice period.
            end_date: The end date for the invoice period.
            customer_id: Optional customer ID to limit to a specific customer.

        Returns:
            A list of generated invoices.
        """
        invoices = []
        # If no customer specified or billing periods found, we might want to generate
        # invoices directly for customers who don't have billing periods but have usage
        if not customer_id:
            # Find customers with usage in this period but no billing periods
            customers_with_usage = (
                self.db.query(Customer.id)
                .join(UsageEvent, Customer.id == UsageEvent.customer_id)
                .filter(
                    UsageEvent.event_time >= start_date,
                    UsageEvent.event_time <= end_date,
                )
                .distinct()
                .all()
            )

            for customer_row in customers_with_usage:
                customer_id = customer_row[0]

                # Check if this customer already has an invoice from a billing period in this range
                customer_has_invoice = False
                for invoice in invoices:
                    if invoice.customer_id == customer_id:
                        customer_has_invoice = True
                        break

                if not customer_has_invoice:
                    # Generate a pure usage-based invoice for this customer
                    invoice = self.generate_invoice_for_date_range(
                        customer_id, start_date, end_date
                    )
                    invoices.append(invoice)

        # If a specific customer is requested and no billing periods found, generate a direct invoice
        elif customer_id:
            # Check if customer exists
            customer = (
                self.db.query(Customer).filter(Customer.id == customer_id).first()
            )
            if customer:
                # Generate a pure usage-based invoice for this customer
                invoice = self.generate_invoice_for_date_range(
                    customer_id, start_date, end_date
                )
                invoices.append(invoice)

        return invoices

    def create_billing_periods(self, subscription: Subscription) -> List[BillingPeriod]:
        """
        Creates billing periods for a subscription based on its billing frequency.

        Args:
            subscription: The subscription to create billing periods for.

        Returns:
            A list of created billing periods.
        """
        plan = subscription.plan
        start_date = subscription.start_date
        end_date = subscription.end_date or (
            subscription.start_date + timedelta(days=365 * 10)
        )  # Far future if ongoing

        billing_periods = []

        current_start = start_date

        while current_start < end_date:
            # Calculate period end based on frequency
            if plan.billing_frequency == "monthly":
                # Add 1 month (approximately)
                year = current_start.year + (current_start.month // 12)
                month = (current_start.month % 12) + 1
                current_end = datetime(year, month, current_start.day)

            elif plan.billing_frequency == "quarterly":
                # Add 3 months (approximately)
                year = current_start.year + (current_start.month + 2) // 12
                month = ((current_start.month + 2) % 12) + 1
                current_end = datetime(year, month, current_start.day)

            elif plan.billing_frequency == "yearly":
                # Add 1 year
                current_end = datetime(
                    current_start.year + 1, current_start.month, current_start.day
                )
            else:
                # Default to monthly
                year = current_start.year + (current_start.month // 12)
                month = (current_start.month % 12) + 1
                current_end = datetime(year, month, current_start.day)

            # Ensure end date doesn't exceed subscription end date
            if current_end > end_date:
                current_end = end_date

            # Create a billing period
            period = BillingPeriod(
                subscription_id=subscription.id,
                start_date=current_start,
                end_date=current_end,
            )

            self.db.add(period)
            billing_periods.append(period)

            # Move to next period
            current_start = current_end

        self.db.commit()
        return billing_periods
