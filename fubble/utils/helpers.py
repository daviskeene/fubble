from datetime import datetime, date
from typing import Dict, Any, Union, Optional
import json
import uuid
import re


def generate_unique_id(prefix: str = "") -> str:
    """
    Generates a unique ID with an optional prefix.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        A unique ID string.
    """
    unique_id = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}{unique_id}" if prefix else unique_id


def is_valid_email(email: str) -> bool:
    """
    Validates an email address format.

    Args:
        email: The email address to validate.

    Returns:
        True if the email format is valid, False otherwise.
    """
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Formats a currency amount.

    Args:
        amount: The amount to format.
        currency: The currency code.

    Returns:
        A formatted currency string.
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    elif currency == "GBP":
        return f"£{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_date(date_obj: Union[datetime, date], format_str: str = "%Y-%m-%d") -> str:
    """
    Formats a date or datetime object as a string.

    Args:
        date_obj: The date or datetime to format.
        format_str: The format string to use.

    Returns:
        A formatted date string.
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_str)
    elif isinstance(date_obj, date):
        return date_obj.strftime(format_str)
    else:
        raise ValueError("Expected datetime or date object")


def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
    """
    Parses a date string into a datetime object.

    Args:
        date_str: The date string to parse.
        format_str: The format string to use.

    Returns:
        A datetime object.
    """
    return datetime.strptime(date_str, format_str)


def serialize_to_json(data: Any) -> str:
    """
    Serializes data to a JSON string, handling dates and other types.

    Args:
        data: The data to serialize.

    Returns:
        A JSON string.
    """

    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    return json.dumps(data, default=json_serial)


def deserialize_from_json(json_str: str) -> Any:
    """
    Deserializes a JSON string to Python data.

    Args:
        json_str: The JSON string to deserialize.

    Returns:
        The deserialized data.
    """
    return json.loads(json_str)


def calculate_proration(amount: float, total_days: int, used_days: int) -> float:
    """
    Calculates a prorated amount based on days used.

    Args:
        amount: The full amount.
        total_days: The total number of days in the period.
        used_days: The number of days used.

    Returns:
        The prorated amount.
    """
    if total_days <= 0:
        return 0

    return amount * (used_days / total_days)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncates a string to a maximum length.

    Args:
        text: The string to truncate.
        max_length: The maximum length.
        suffix: The suffix to add to truncated strings.

    Returns:
        The truncated string.
    """
    if len(text) <= max_length:
        return text
    else:
        return text[: max_length - len(suffix)] + suffix
