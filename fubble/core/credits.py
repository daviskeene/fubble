from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from fubble.database.models import (
    Customer,
    CreditBalance,
    CreditStatus,
    CreditTransaction,
    CreditType,
)


class CreditManager:
    """
    Manages customer credit balances and transactions.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_credits(
        self,
        customer_id: int,
        amount: float,
        credit_type: str = "prepaid",
        description: str = None,
        expires_in_days: Optional[int] = None,
        subscription_id: Optional[int] = None,
        invoice_id: Optional[int] = None,
    ) -> Optional[CreditBalance]:
        """
        Adds credits to a customer's account.

        Args:
            customer_id: The customer's ID.
            amount: The amount of credits to add.
            credit_type: Type of credit (prepaid, refund, promotional, adjustment).
            description: Optional description of the credit.
            expires_in_days: Optional number of days until expiration.
            subscription_id: Optional associated subscription ID.
            invoice_id: Optional associated invoice ID.

        Returns:
            The created CreditBalance object if successful, None otherwise.
        """
        # Validate customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        # Validate amount
        if amount <= 0:
            return None

        # Validate credit type
        if credit_type not in [t.value for t in CreditType]:
            credit_type = CreditType.PREPAID

        # Calculate expiration date
        expires_at = None
        if expires_in_days is not None and expires_in_days > 0:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create credit balance
        credit_balance = CreditBalance(
            customer_id=customer_id,
            amount=amount,
            remaining_amount=amount,
            credit_type=credit_type,
            status=CreditStatus.ACTIVE,
            expires_at=expires_at,
            description=description,
            subscription_id=subscription_id,
            invoice_id=invoice_id,
        )

        self.db.add(credit_balance)

        # Create initial transaction record
        transaction = CreditTransaction(
            credit_balance_id=credit_balance.id,
            amount=amount,
            description=f"Initial credit: {description or 'Added credits'}",
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(credit_balance)

        return credit_balance

    def get_customer_credit_balance(self, customer_id: int) -> float:
        """
        Gets the total active credit balance for a customer.

        Args:
            customer_id: The customer's ID.

        Returns:
            The total remaining active credit amount.
        """
        # Get all active credits for the customer
        active_credits = (
            self.db.query(CreditBalance)
            .filter(
                CreditBalance.customer_id == customer_id,
                CreditBalance.status == CreditStatus.ACTIVE,
                CreditBalance.remaining_amount > 0,
                (
                    CreditBalance.expires_at.is_(None)
                    | (CreditBalance.expires_at > datetime.utcnow())
                ),
            )
            .all()
        )

        # Sum remaining amounts
        total_credits = sum(credit.remaining_amount for credit in active_credits)

        return total_credits

    def get_customer_credit_balances(
        self, customer_id: int, include_expired: bool = False
    ) -> List[CreditBalance]:
        """
        Gets all credit balances for a customer.

        Args:
            customer_id: The customer's ID.
            include_expired: Whether to include expired/consumed credits.

        Returns:
            List of CreditBalance objects.
        """
        query = self.db.query(CreditBalance).filter(
            CreditBalance.customer_id == customer_id
        )

        if not include_expired:
            query = query.filter(
                CreditBalance.status == CreditStatus.ACTIVE,
                (
                    CreditBalance.expires_at.is_(None)
                    | (CreditBalance.expires_at > datetime.utcnow())
                ),
            )

        return query.order_by(CreditBalance.created_at.desc()).all()

    def apply_credits_manually(
        self,
        customer_id: int,
        amount: float,
        description: str,
        invoice_id: Optional[int] = None,
    ) -> bool:
        """
        Manually applies credits from a customer's balance.

        Args:
            customer_id: The customer's ID.
            amount: The amount of credits to apply.
            description: Description of the application.
            invoice_id: Optional invoice ID to associate with the transaction.

        Returns:
            True if successful, False otherwise.
        """
        # Check if customer has enough credits
        available_credits = self.get_customer_credit_balance(customer_id)
        if available_credits < amount:
            return False

        # Get active credits, ordered by expiration date (soonest first)
        active_credits = (
            self.db.query(CreditBalance)
            .filter(
                CreditBalance.customer_id == customer_id,
                CreditBalance.status == CreditStatus.ACTIVE,
                CreditBalance.remaining_amount > 0,
                (
                    CreditBalance.expires_at.is_(None)
                    | (CreditBalance.expires_at > datetime.utcnow())
                ),
            )
            .order_by(CreditBalance.expires_at.asc())
            .all()
        )

        remaining_amount = amount

        for credit in active_credits:
            if remaining_amount <= 0:
                break

            # Determine amount to apply from this credit
            amount_to_apply = min(credit.remaining_amount, remaining_amount)

            # Update credit balance
            credit.remaining_amount -= amount_to_apply
            if credit.remaining_amount <= 0:
                credit.status = CreditStatus.CONSUMED

            # Create transaction record
            transaction = CreditTransaction(
                credit_balance_id=credit.id,
                amount=-amount_to_apply,  # Negative because it's a deduction
                description=description,
                invoice_id=invoice_id,
            )

            self.db.add(transaction)

            # Update remaining amount
            remaining_amount -= amount_to_apply

        self.db.commit()
        return True

    def expire_credits(self) -> int:
        """
        Expires credits that have passed their expiration date.

        Returns:
            Number of credit balances that were expired.
        """
        now = datetime.utcnow()

        # Find credits that should be expired
        expired_credits = (
            self.db.query(CreditBalance)
            .filter(
                CreditBalance.status == CreditStatus.ACTIVE,
                CreditBalance.expires_at <= now,
            )
            .all()
        )

        count = 0
        for credit in expired_credits:
            credit.status = CreditStatus.EXPIRED

            # Create transaction record for the expiration
            if credit.remaining_amount > 0:
                transaction = CreditTransaction(
                    credit_balance_id=credit.id,
                    amount=-credit.remaining_amount,  # Negative because it's a deduction
                    description="Credits expired",
                )

                self.db.add(transaction)
                count += 1

        self.db.commit()
        return count
