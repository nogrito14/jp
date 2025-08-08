import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional


def parse_brazilian_date(text: str) -> Optional[date]:
    if not text:
        return None
    text = text.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_currency_to_decimal(text: str) -> Decimal:
    if text is None:
        return Decimal("0")
    cleaned = re.sub(r"[^0-9,.-]", "", text)
    if cleaned.count(",") == 1 and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def normalize_phone_to_e164(phone: Optional[str], default_country_code: str = "55") -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("+"):
        digits = digits[1:]
    if digits.startswith(default_country_code):
        return f"+{digits}"
    return f"+{default_country_code}{digits}"