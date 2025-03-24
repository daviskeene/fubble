from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from fubble.database.models import (
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Customer,
)
from fubble.config import settings


class InvoiceManager:
    """
    Handles invoice generation, management, and operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """
        Gets an invoice by ID.

        :param invoice_id: The invoice's ID.
        :return: The Invoice object if found, None otherwise.
        """
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def get_customer_invoices(
        self, customer_id: int, status: Optional[str] = None
    ) -> List[Invoice]:
        """
        Gets invoices for a customer, optionally filtered by status.

        :param customer_id: The customer's ID.
        :param status: Optional invoice status to filter by.

        :return: List of Invoice objects.
        """
        query = self.db.query(Invoice).filter(Invoice.customer_id == customer_id)

        if status:
            query = query.filter(Invoice.status == status)

        return query.order_by(Invoice.issue_date.desc()).all()

    def get_invoices_by_status(self, status: str) -> List[Invoice]:
        """
        Gets all invoices with a specific status.

        :param status: The invoice status to filter by.
        :return: List of Invoice objects.
        """
        return (
            self.db.query(Invoice)
            .filter(Invoice.status == status)
            .order_by(Invoice.issue_date.desc())
            .all()
        )

    def update_invoice_status(self, invoice_id: int, status: str) -> Optional[Invoice]:
        """
        Updates an invoice's status.

        :param invoice_id: The invoice's ID.
        :param status: The new status.
        :return: The updated Invoice object if found, None otherwise.
        """
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None

        # Validate status
        if status not in [s.value for s in InvoiceStatus]:
            return None

        invoice.status = status

        # Update paid date if status is "paid"
        if status == "paid":
            invoice.paid_date = datetime.utcnow()

        invoice.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def add_invoice_item(
        self,
        invoice_id: int,
        description: str,
        amount: float,
        quantity: Optional[float] = None,
        metric_name: Optional[str] = None,
        unit_price: Optional[float] = None,
    ) -> Optional[InvoiceItem]:
        """
        Adds an item to an invoice.

        :param invoice_id: The invoice's ID.
        :param description: Description of the item.
        :param amount: Total amount for the item.
        :param quantity: Optional quantity.
        :param metric_name: Optional metric name.
        :param unit_price: Optional unit price.
        :return: The created InvoiceItem if successful, None otherwise.
        """
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None

        # Only allow adding items to draft invoices
        if invoice.status != InvoiceStatus.DRAFT:
            return None

        # Calculate unit price if not provided
        if unit_price is None and quantity is not None and quantity > 0:
            unit_price = amount / quantity
        elif unit_price is None:
            unit_price = amount

        # Create invoice item
        invoice_item = InvoiceItem(
            invoice_id=invoice_id,
            description=description,
            metric_name=metric_name,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
        )

        self.db.add(invoice_item)

        # Update invoice total
        invoice.amount += amount
        invoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice_item)

        return invoice_item

    def remove_invoice_item(self, item_id: int) -> bool:
        """
        Removes an item from an invoice.

        :param item_id: The invoice item's ID.
        :return: True if successful, False otherwise.
        """
        item = self.db.query(InvoiceItem).filter(InvoiceItem.id == item_id).first()

        if not item:
            return False

        invoice = self.get_invoice(item.invoice_id)
        if not invoice or invoice.status != InvoiceStatus.DRAFT:
            return False

        # Update invoice total
        invoice.amount -= item.amount
        invoice.updated_at = datetime.utcnow()

        # Delete the item
        self.db.delete(item)
        self.db.commit()

        return True

    def finalize_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """
        Finalizes an invoice, changing its status from draft to pending.

        :param invoice_id: The invoice's ID.
        :return: The updated Invoice object if successful, None otherwise.
        """
        invoice = self.get_invoice(invoice_id)
        if not invoice or invoice.status != InvoiceStatus.DRAFT:
            return None

        invoice.status = InvoiceStatus.PENDING
        invoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def void_invoice(
        self, invoice_id: int, reason: Optional[str] = None
    ) -> Optional[Invoice]:
        """
        Voids an invoice.

        :param invoice_id: The invoice's ID.
        :param reason: Optional reason for voiding.
        :return: The updated Invoice object if successful, None otherwise.
        """
        invoice = self.get_invoice(invoice_id)
        if not invoice or invoice.status == InvoiceStatus.PAID:
            return None

        invoice.status = InvoiceStatus.VOID
        invoice.updated_at = datetime.utcnow()

        if reason:
            invoice.notes = f"{invoice.notes or ''}\nVoided: {reason}"

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def create_empty_invoice(
        self,
        customer_id: int,
        issue_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Optional[Invoice]:
        """
        Creates an empty invoice for a customer.

        :param customer_id: The customer's ID.
        :param issue_date: When the invoice is issued (defaults to now).
        :param due_date: When the invoice is due (defaults to issue_date + payment term).
        :param notes: Optional notes for the invoice.

        :return: The created Invoice object if successful, None otherwise.
        """
        # Check if customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        # Set default dates
        if issue_date is None:
            issue_date = datetime.utcnow()

        if due_date is None:
            due_date = issue_date + timedelta(days=settings.DEFAULT_PAYMENT_TERM_DAYS)

        # Generate invoice number
        invoice_number = f"INV-{issue_date.strftime('%Y%m%d')}-{customer_id}-{int(datetime.utcnow().timestamp())}"

        # Create the invoice
        invoice = Invoice(
            customer_id=customer_id,
            invoice_number=invoice_number,
            status=InvoiceStatus.DRAFT,
            issue_date=issue_date,
            due_date=due_date,
            amount=0,
            notes=notes,
        )

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        return invoice
