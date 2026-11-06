import re
from datetime import date


MAX_AMOUNT_PENCE = 9_223_372_036_854_775_807


def parse_amount(amount_text):
    """Convert a positive monetary amount into integer pence."""
    amount_text = amount_text.strip()

    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", amount_text):
        raise ValueError(
            "Enter an amount such as 12, 12.50, or 0.99."
        )

    pounds, separator, pence = amount_text.partition(".")

    # Complete a single decimal digit: "5" becomes "50".
    pence = pence.ljust(2, "0")

    # Reject oversized input before converting it to an integer.
    digits = (pounds + pence).lstrip("0") or "0"

    if len(digits) > 19:
        raise ValueError("The amount is too large.")

    amount_pence = int(digits)

    if amount_pence <= 0:
        raise ValueError("The amount must be greater than zero.")

    if amount_pence > MAX_AMOUNT_PENCE:
        raise ValueError("The amount is too large.")

    return amount_pence


def parse_date(date_text):
    """Validate a calendar date and return YYYY-MM-DD text."""
    date_text = date_text.strip()

    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_text):
        raise ValueError("Enter the date as YYYY-MM-DD.")

    try:
        date.fromisoformat(date_text)
    except ValueError:
        raise ValueError("Enter a real calendar date.") from None

    return date_text


def format_money(amount_pence):
    """Format integer pence without converting through float."""
    sign = "-" if amount_pence < 0 else ""
    pounds, pence = divmod(abs(amount_pence), 100)

    return f"{sign}£{pounds:,}.{pence:02d}"