"""SYNTHETIC test values for the personal-data guardrails. Never real data.

Every value here is reserved or published for testing:
- e-mail: the RFC 2606 reserved domain example.com
- phone numbers: the 555-0100 to 555-0199 range, reserved for fictional use
- card number: a number the card networks publish for testing (passes the Luhn check)

This is the ONLY file in the project that contains them. Tests import these constants.
Docs describe them by kind instead of repeating them.
"""

FAKE_EMAIL = "jane.doe@example.com"
FAKE_PHONE = "212-555-0123"
FAKE_PHONE_SPACED = "(212) 555 0187"
FAKE_CARD = "4111111111111111"
FAKE_CARD_SPACED = "4111 1111 1111 1111"
NOT_A_CARD = "1234567812345678"  # 16 digits that FAIL the Luhn check: must not be redacted
