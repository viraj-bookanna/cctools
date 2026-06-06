# cctools

Credit card validation, type detection, and detail extraction utilities for Python.

## Features

- **Card type detection** -- identify Visa, MasterCard, American Express, and Discover cards by number.
- **Luhn validation** -- verify card numbers using the Luhn checksum algorithm.
- **Detail extraction** -- parse card number, expiry date, and CVV from unstructured text (OCR output, chat messages, pasted forms, etc.).
- **Unicode normalization** -- handles accented or non-ASCII digits via `unidecode`.

## Installation

Requires Python 3.10+.

```bash
# With uv
uv add cctools

# With pip (from source)
pip install .
```

For development:

```bash
git clone https://github.com/viraj-bookanna/cctools.git
cd cctools
uv sync
```

## Quick Start

```python
from cctools import cc_type, luhn, find_cc
```

### Identify a card brand

```python
card = cc_type("4111111111111111")
print(card.name)        # "Visa"
print(card.cvv_length)  # 3
```

### Validate a card number

```python
luhn("4111111111111111")  # True
luhn("1234567890123456")  # False
```

Spaces and dashes are stripped automatically:

```python
luhn("4111-1111-1111-1111")  # True
```

### Extract card details from text

```python
result = find_cc("card 4111111111111111 exp 12/26 cvv 123")
print(result)
# CardDetails(number='4111111111111111', month='12', year='2026', cvv='123')
```

`find_cc` returns `None` when the text doesn't contain valid card details.

## API Reference

### `cc_type(card_number: str) -> CardType`

Returns a `CardType` dataclass for the matched brand, or `UNKNOWN_CARD` if no
pattern matches.

**`CardType` fields:**

| Field        | Type  | Description                        |
|--------------|-------|------------------------------------|
| `key`        | `str` | Lowercase identifier (e.g. `visa`) |
| `name`       | `str` | Display name (e.g. `Visa`)         |
| `regex`      | `str` | Validation regex pattern           |
| `cvv_length` | `int` | Expected CVV digit count (3 or 4)  |

### `luhn(n: str | int) -> bool`

Returns `True` if the number passes the Luhn checksum. Accepts strings or
integers; spaces, dashes, and dots are stripped before validation.

### `find_cc(text: str) -> CardDetails | None`

Scans free-form text for a Luhn-valid card number, an expiration date, and a
CVV. Returns a `CardDetails` named tuple or `None`.

**`CardDetails` fields:**

| Field    | Type  | Example    |
|----------|-------|------------|
| `number` | `str` | `"4111111111111111"` |
| `month`  | `str` | `"12"` (zero-padded) |
| `year`   | `str` | `"2026"` (four-digit) |
| `cvv`    | `str` | `"123"` |

## CLI

After installation, a `cctools` command is available:

```bash
cctools 4111111111111111
# Number : 4111111111111111
# Type   : Visa
# Valid  : Yes
```

## Supported Card Types

| Brand            | Prefix(es)       | Length | CVV Length |
|------------------|------------------|--------|-----------|
| Visa             | 4                | 16     | 3         |
| MasterCard       | 51-55, 2221-2720 | 16     | 3         |
| American Express | 34, 37           | 15     | 4         |
| Discover         | 6011, 622, 64-65 | 16     | 3         |

## License

[GPL-3.0](LICENSE)
