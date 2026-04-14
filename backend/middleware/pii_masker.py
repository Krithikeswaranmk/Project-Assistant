import re

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "api_key": r"\b[A-Za-z0-9_-]{20,}\b",
}


def mask_pii(text: str) -> tuple[str, dict]:
    mapping: dict[str, str] = {}
    masked_text = text

    for pii_type, pattern in PII_PATTERNS.items():
        counter = 0

        def replacer(match: re.Match) -> str:
            nonlocal counter
            counter += 1
            key = f"[{pii_type.upper()}_{counter}]"
            mapping[key] = match.group(0)
            return key

        masked_text = re.sub(pattern, replacer, masked_text)

    return masked_text, mapping


def unmask_pii(text: str, mapping: dict) -> str:
    unmasked = text
    for placeholder, original in mapping.items():
        unmasked = unmasked.replace(placeholder, original)
    return unmasked
