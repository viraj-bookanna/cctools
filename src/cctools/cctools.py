"""Credit card validation, type detection, and detail extraction utilities."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

from unidecode import unidecode


@dataclass(frozen=True)
class CardType:
    """A recognized credit card brand with its validation pattern."""

    key: str
    name: str
    regex: str
    cvv_length: int


UNKNOWN_CARD = CardType(key="unknown", name="Unknown", regex="", cvv_length=0)

CARD_TYPES: dict[str, CardType] = {
    "visa": CardType(
        key="visa",
        name="Visa",
        regex=r"^4\d{15}$",
        cvv_length=3,
    ),
    "mastercard": CardType(
        key="mastercard",
        name="MasterCard",
        regex=r"^5[1-5]\d{14}$|^2(?:2(?:2[1-9]|[3-9]\d)|[3-6]\d\d|7(?:[01]\d|20))\d{12}$",
        cvv_length=3,
    ),
    "americanexpress": CardType(
        key="americanexpress",
        name="American Express",
        regex=r"^3[47]\d{13}$",
        cvv_length=4,
    ),
    "discovercard": CardType(
        key="discovercard",
        name="Discover",
        regex=(
            r"^(?=6011|622(12[6-9]|1[3-9][0-9]|[2-8][0-9]{2}"
            r"|9[0-1][0-9]|92[0-5]|64[4-9])|65)\d{16}$"
        ),
        cvv_length=3,
    ),
}


def _normalize(card_number: str) -> str:
    """Strip spaces, dashes, and dots from a card number string."""
    return re.sub(r"[\s\-.]", "", card_number)


def cc_type(card_number: str) -> CardType:
    """Identify the card brand by its number.

    Args:
        card_number: The credit card number (spaces/dashes are stripped
            automatically).

    Returns:
        A ``CardType`` for the matched brand, or ``UNKNOWN_CARD``.
    """
    cleaned = _normalize(card_number)
    for card in CARD_TYPES.values():
        if re.match(card.regex, cleaned):
            return card
    return UNKNOWN_CARD


def luhn(n: str | int) -> bool:
    """Validate a number using the Luhn checksum algorithm.

    Args:
        n: Card number as a string or integer.

    Returns:
        ``True`` if the checksum is valid.
    """
    digits = [int(ch) for ch in _normalize(str(n))][::-1]
    checksum = sum(digits[0::2]) + sum(sum(divmod(d * 2, 10)) for d in digits[1::2])
    return checksum % 10 == 0


class CardDetails(NamedTuple):
    """Parsed credit card details extracted from text."""

    number: str
    month: str  # zero-padded, e.g. "01"
    year: str  # four-digit, e.g. "2026"
    cvv: str


# Matches a 15–20 digit card number surrounded by non-digit boundaries.
_CC_PATTERN = re.compile(r"(?:^|[^0-9])(\d{15,20})(?:[^0-9]|$)")

# Expiry in MM<sep>YY or YY<sep>MM or YYYY<sep>MM forms.
_EXP_PATTERN = re.compile(
    r"(?:^|[^0-9])"
    r"(?:"
    r"(?:(\d{2}|20\d{2})([^0-9a-zA-Z])\2*?(\d{2}))"
    r"|"
    r"(?:(\d{2})([^0-9a-zA-Z])\5*?(\d{2}|20\d{2}))"
    r")"
    r"(?:[^0-9]|$)"
)

# Compact expiry without a separator, e.g. "0126" or "012026".
_EXP_COMPACT_PATTERN = re.compile(
    r"(?:^|[^0-9])(?:(0\d|1[012])((?:20)?[23]\d))(?:[^0-9]|$)"
)


def find_cc(text: str) -> CardDetails | None:
    """Extract credit card number, expiry, and CVV from free-form text.

    The text is Unicode-normalized first, then scanned for a Luhn-valid
    card number, an expiration date, and a CVV whose length matches the
    detected card brand.

    Args:
        text: Unstructured input that may contain card details.

    Returns:
        A ``CardDetails`` named tuple, or ``None`` if extraction fails.
    """
    text = unidecode(text)

    cc_match = _CC_PATTERN.search(text)
    if not cc_match:
        cc_match = _CC_PATTERN.search(re.sub(r"\s(\d{4})", r"\1", text))

    exp_match = _EXP_PATTERN.search(text)
    if not exp_match:
        exp_match = _EXP_PATTERN.search(text.replace(" ", ""))
    if not exp_match:
        compact = _EXP_COMPACT_PATTERN.search(text)
        if compact:
            exp_match = _EXP_PATTERN.search(f"{compact[1]}|{compact[2]}")

    if not cc_match or not exp_match or not luhn(cc_match[1]):
        return None

    card = cc_type(cc_match[1])
    cvv_pattern = re.compile(rf"(?:^|[^0-9])(\d{{{card.cvv_length}}})(?:[^0-9]|$)")
    cvv_match = cvv_pattern.search(text)
    if not cvv_match:
        return None

    part_a = exp_match[1] or exp_match[4]
    part_b = exp_match[3] or exp_match[6]

    if len(part_a) == 4 or not part_a.startswith(("0", "1")):
        year_raw, month_raw = part_a, part_b
    else:
        year_raw, month_raw = part_b, part_a

    month = f"0{month_raw}"[-2:]
    century = str(datetime.now().year)[:2]
    year = year_raw if len(year_raw) == 4 else f"{century}{year_raw}"

    return CardDetails(
        number=cc_match[1],
        month=month,
        year=year,
        cvv=cvv_match[1],
    )


def main() -> None:
    """CLI entry point: validate and identify a card number."""
    if len(sys.argv) < 2:
        print("Usage: cctools <card_number>")
        sys.exit(1)

    number = _normalize(sys.argv[1])
    card = cc_type(number)
    valid = luhn(number)

    print(f"Number : {number}")
    print(f"Type   : {card.name}")
    print(f"Valid  : {'Yes' if valid else 'No'}")
